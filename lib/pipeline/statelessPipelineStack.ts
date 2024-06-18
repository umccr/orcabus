import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as chatbot from 'aws-cdk-lib/aws-chatbot';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codestarnotifications from 'aws-cdk-lib/aws-codestarnotifications';

import {
  StatelessStackCollection,
  StatelessStackCollectionProps,
} from '../workload/stateless/statelessStackCollectionClass';

import { getEnvironmentConfig } from '../../config/config';
import { AppStage } from '../../config/constants';

export class StatelessPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // Define CodeBuild project for GH action runner to use
    // the GH repo defined below already configured to allow CB webhook
    // This is actually not part of the pipeline, so I guess we could move this someday.
    const ghRunnerRole = new iam.Role(this, 'GHRunnerRole', {
      assumedBy: new iam.ServicePrincipal('codebuild.amazonaws.com'),
    });
    new codebuild.CfnProject(this, 'GHRunnerCodeBuildProject', {
      // the name here act as a unique id for GH action to know which CodeBuild to use
      // So if you change this, you need to update the GH action .yml file (.github/workflows/prbuild.yml)
      name: 'orcabus-codebuild-gh-runner',
      description: 'GitHub Action Runner in CodeBuild for `orcabus` repository',
      serviceRole: ghRunnerRole.roleArn,
      artifacts: {
        type: 'NO_ARTIFACTS',
      },
      environment: {
        type: 'ARM_CONTAINER',
        computeType: 'BUILD_GENERAL1_LARGE',
        image: 'aws/codebuild/amazonlinux2-aarch64-standard:3.0',
        privilegedMode: true,
      },
      source: {
        type: 'GITHUB',
        gitCloneDepth: 1,
        location: 'https://github.com/umccr/orcabus.git',
        reportBuildStatus: false,
      },
      logsConfig: { cloudWatchLogs: { status: 'DISABLED' } },
      triggers: {
        webhook: true,
        buildType: 'BUILD',
        filterGroups: [[{ type: 'EVENT', pattern: 'WORKFLOW_JOB_QUEUED' }]],
      },
    });

    // A connection where the pipeline get its source code
    const codeStarArn = ssm.StringParameter.valueForStringParameter(this, 'codestar_github_arn');
    const sourceFile = pipelines.CodePipelineSource.connection('umccr/orcabus', 'main', {
      connectionArn: codeStarArn,
    });

    const unitTest = new pipelines.CodeBuildStep('UnitTest', {
      installCommands: [
        //  RUST installation
        `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y`,
        `source $HOME/.cargo/env`,
        `pip3 install cargo-lambda`,
      ],
      commands: ['yarn install --immutable', 'make test-stateless', 'make test-suite'],
      input: sourceFile,
      primaryOutputDirectory: '.',
      buildEnvironment: {
        privileged: true,
        computeType: codebuild.ComputeType.LARGE,
        buildImage: codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
        environmentVariables: {
          NODE_OPTIONS: {
            value: '--max-old-space-size=8192',
          },
        },
      },
      partialBuildSpec: codebuild.BuildSpec.fromObject({
        reports: {
          'orcabus-infrastructureStatelessReports': {
            files: ['target/report/*.xml'],
            'file-format': 'JUNITXML',
          },
          'orcabus-microserviceReports': {
            files: ['lib/workload/**/target/report/*.xml'],
            'file-format': 'JUNITXML',
          },
        },
        version: '0.2',
      }),
    });

    const synthAction = new pipelines.CodeBuildStep('Synth', {
      installCommands: [
        //  RUST installation
        `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y`,
        `source $HOME/.cargo/env`,
        `pip3 install cargo-lambda`,
      ],
      commands: ['yarn install --immutable', 'yarn run cdk-stateless synth'],
      input: unitTest,
      primaryOutputDirectory: 'cdk.out',
      rolePolicyStatements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ['sts:AssumeRole'],
          resources: ['*'],
        }),
      ],
    });

    const pipeline = new pipelines.CodePipeline(this, 'Pipeline', {
      synth: synthAction,
      selfMutation: true,
      crossAccountKeys: true,
      dockerEnabledForSynth: true,
      dockerEnabledForSelfMutation: true,
      codeBuildDefaults: {
        buildEnvironment: {
          computeType: codebuild.ComputeType.LARGE,
          buildImage: codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
          environmentVariables: {
            NODE_OPTIONS: {
              value: '--max-old-space-size=8192',
            },
          },
        },
      },
    });

    // After the assets are published, this could be removed to prevent hitting artifact limit
    // https://github.com/aws/aws-cdk/issues/9917
    const stripAssetsFromAssembly = new pipelines.CodeBuildStep('StripAssetsFromAssembly', {
      input: pipeline.cloudAssemblyFileSet,
      commands: [
        'S3_PATH=${CODEBUILD_SOURCE_VERSION#"arn:aws:s3:::"}',
        'ZIP_ARCHIVE=$(basename $S3_PATH)',
        'echo $S3_PATH',
        'echo $ZIP_ARCHIVE',
        'ls',
        'rm -rfv asset.*',
        'zip -r -q -A $ZIP_ARCHIVE *',
        'ls',
        'aws s3 cp $ZIP_ARCHIVE s3://$S3_PATH',
      ],
    });

    /**
     * Deployment to Beta (Dev) account
     */
    const betaConfig = getEnvironmentConfig(AppStage.BETA);
    if (!betaConfig) throw new Error(`No 'Beta' account configuration`);
    pipeline.addStage(
      new OrcaBusStatelessDeploymentStage(
        this,
        'OrcaBusBeta',
        betaConfig.stackProps.statelessConfig,
        {
          account: betaConfig.accountId,
          region: betaConfig.region,
        }
      ),
      { pre: [stripAssetsFromAssembly] } // I think this should only be done once across stages
    );

    // Since the stateless stack might need to reference the stateful resources (e.g. db, sg), we might comment this out
    // to prevent cdk from looking up for non existence resource. Currently the stateful resource is only deployed in
    // dev

    // /**
    //  * Deployment to Gamma (Staging) account
    //  */
    // const gammaConfig = getEnvironmentConfig(AppStage.GAMMA);
    // if (!gammaConfig) throw new Error(`No 'Gamma' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusStatelessDeploymentStage(
    //     this,
    //     'OrcaBusGamma',
    //     gammaConfig.stackProps.statelessConfig,
    //     {
    //       account: gammaConfig.accountId,
    //       region: gammaConfig.region,
    //     }
    //   ),
    //   { pre: [new pipelines.ManualApprovalStep('PromoteToGamma')] }
    // );

    // /**
    //  * Deployment to Prod account
    //  */
    // const prodConfig = getEnvironmentConfig(AppStage.PROD);
    // if (!prodConfig) throw new Error(`No 'Prod' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusStatelessDeploymentStage(
    //     this,
    //     'OrcaBusProd',
    //     prodConfig.stackProps.statelessConfig,
    //     {
    //       account: prodConfig.accountId,
    //       region: prodConfig.region,
    //     }
    //   ),
    //   { pre: [new pipelines.ManualApprovalStep('PromoteToProd')] }
    // );

    // need to build pipeline so we could add notification at the pipeline construct
    pipeline.buildPipeline();

    pipeline.pipeline.artifactBucket.grantReadWrite(stripAssetsFromAssembly.project);

    // notification for success/failure
    const alertsBuildSlackConfigArn = ssm.StringParameter.valueForStringParameter(
      this,
      '/chatbot_arn/slack/alerts-build'
    );
    const target = chatbot.SlackChannelConfiguration.fromSlackChannelConfigurationArn(
      this,
      'SlackChannelConfiguration',
      alertsBuildSlackConfigArn
    );

    pipeline.pipeline.notifyOn('PipelineSlackNotification', target, {
      events: [
        codepipeline.PipelineNotificationEvents.PIPELINE_EXECUTION_FAILED,
        codepipeline.PipelineNotificationEvents.PIPELINE_EXECUTION_SUCCEEDED,
      ],
      detailType: codestarnotifications.DetailType.FULL,
      notificationRuleName: 'orcabus_stateless_pipeline_notification',
    });
  }
}

class OrcaBusStatelessDeploymentStage extends cdk.Stage {
  constructor(
    scope: Construct,
    environmentName: string,
    statelessStackCollectionProps: StatelessStackCollectionProps,
    env: cdk.Environment
  ) {
    super(scope, environmentName, { env: env });

    new StatelessStackCollection(this, env, statelessStackCollectionProps);
  }
}
