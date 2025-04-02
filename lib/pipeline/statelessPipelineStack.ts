import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import { ComputeType } from 'aws-cdk-lib/aws-codebuild';
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
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { UiOpenAPITestStep } from './component/uiOpenAPITest';

export class StatelessPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // Define CodeBuild project for GH action runner to use
    // the GH repo defined below already configured to allow CB webhook
    // This is actually not part of the pipeline, so I guess we could move this someday.
    const projectName = 'orcabus-codebuild-gh-runner';
    const testEventPolicy = new iam.PolicyStatement({
      actions: ['events:TestEventPattern'],
      resources: ['*'],
    });
    const project = new codebuild.Project(this, 'GHRunnerCodeBuildProject', {
      projectName,
      description: 'GitHub Action Runner in CodeBuild for `orcabus` repository',
      environment: {
        buildImage: codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
        computeType: ComputeType.LARGE,
        privileged: true,
      },
      source: codebuild.Source.gitHub({
        cloneDepth: 1,
        reportBuildStatus: false,
        owner: 'umccr',
        repo: 'orcabus',
        webhook: true,
        webhookFilters: [
          codebuild.FilterGroup.inEventOf(codebuild.EventAction.WORKFLOW_JOB_QUEUED),
        ],
      }),
      logging: {
        cloudWatch: {
          enabled: true,
          logGroup: new LogGroup(this, 'GHRunnerCodeBuildLogGroup', {
            logGroupName: `/aws/codebuild/${projectName}`,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            retention: RetentionDays.TWO_WEEKS,
          }),
        },
      },
    });
    project.addToRolePolicy(testEventPolicy);

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
        'rustup component add rustfmt',
        `pip3 install cargo-lambda`,
      ],
      commands: [
        'corepack enable',
        'yarn install --immutable',
        'make test-stateless-iac',
        'make test-stateless-app-suite',
      ],
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
      rolePolicyStatements: [testEventPolicy],
      partialBuildSpec: codebuild.BuildSpec.fromObject({
        phases: {
          install: {
            'runtime-versions': {
              python: '3.12',
              golang: '1.22',
            },
          },
        },
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
        'rustup component add rustfmt',
        `pip3 install cargo-lambda`,
      ],
      commands: ['corepack enable', 'yarn install --immutable', 'yarn run cdk-stateless synth'],
      input: unitTest,
      primaryOutputDirectory: 'cdk.out',
      rolePolicyStatements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ['sts:AssumeRole'],
          resources: ['*'],
        }),
      ],
      partialBuildSpec: codebuild.BuildSpec.fromObject({
        phases: {
          install: {
            'runtime-versions': {
              // Don't strictly need golang here as CDK can do docker bundling, but `local`
              // bundling tends to be faster.
              golang: '1.22',
            },
          },
        },
        version: '0.2',
      }),
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
     * Deployment to Gamma (Staging) account directly without approval
     */
    const gammaConfig = getEnvironmentConfig(AppStage.GAMMA);
    if (!gammaConfig) throw new Error(`No 'Gamma' account configuration`);
    pipeline.addStage(
      new OrcaBusStatelessDeploymentStage(
        this,
        'OrcaBusGamma',
        gammaConfig.stackProps.statelessConfig,
        {
          account: gammaConfig.accountId,
          region: gammaConfig.region,
        }
      ),
      {
        pre: [stripAssetsFromAssembly],
        post: [new UiOpenAPITestStep(this, 'UiOpenAPITestStep', { testStage: AppStage.GAMMA })],
      }
    );

    /**
     * Deployment to Prod account
     */
    const prodConfig = getEnvironmentConfig(AppStage.PROD);
    if (!prodConfig) throw new Error(`No 'Prod' account configuration`);
    pipeline.addStage(
      new OrcaBusStatelessDeploymentStage(
        this,
        'OrcaBusProd',
        prodConfig.stackProps.statelessConfig,
        {
          account: prodConfig.accountId,
          region: prodConfig.region,
        }
      ),
      { pre: [new pipelines.ManualApprovalStep('PromoteToProd')] }
    );

    /**
     * Deployment to Beta (Dev)
     * This shouldn't be deployed automatically. Some dev work may be deployed manually from local
     * for testing but then could got overwritten by the pipeline if someone has pushed to the main
     * branch. This is put at the end of the pipeline just to have a way of deployment with
     * a click of a button.
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
      { pre: [new pipelines.ManualApprovalStep('PromoteToDev')] }
    );

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
