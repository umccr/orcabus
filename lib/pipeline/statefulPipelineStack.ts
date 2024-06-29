import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as chatbot from 'aws-cdk-lib/aws-chatbot';
import * as codestarnotifications from 'aws-cdk-lib/aws-codestarnotifications';
import { getEnvironmentConfig } from '../../config/config';
import {
  StatefulStackCollectionProps,
  StatefulStackCollection,
} from '../workload/stateful/statefulStackCollectionClass';
import { AppStage } from '../../config/constants';

export class StatefulPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // A connection where the pipeline get its source code
    const codeStarArn = ssm.StringParameter.valueForStringParameter(this, 'codestar_github_arn');
    const sourceFile = pipelines.CodePipelineSource.connection('umccr/orcabus', 'main', {
      connectionArn: codeStarArn,
    });

    const unitTest = new pipelines.CodeBuildStep('UnitTest', {
      commands: [
        'yarn install --immutable',
        'make test-stateful-iac',
        'make test-stateful-app-suite',
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
      partialBuildSpec: codebuild.BuildSpec.fromObject({
        reports: {
          'orcabus-infrastructureStatefulReports': {
            files: ['target/report/*.xml'],
            'file-format': 'JUNITXML',
          },
        },
        version: '0.2',
      }),
    });

    const synthAction = new pipelines.CodeBuildStep('Synth', {
      commands: ['yarn install --immutable', 'yarn run cdk-stateful synth'],
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

    /**
     * Deployment to Beta (Dev) account
     */
    const betaConfig = getEnvironmentConfig(AppStage.BETA);
    if (!betaConfig) throw new Error(`No 'Beta' account configuration`);
    pipeline.addStage(
      new OrcaBusStatefulDeploymentStage(
        this,
        'OrcaBusBeta',
        betaConfig.stackProps.statefulConfig,
        {
          account: betaConfig.accountId,
          region: betaConfig.region,
        }
      )
    );

    /**
     * Deployment to Gamma (Staging) account
     */
    const gammaConfig = getEnvironmentConfig(AppStage.GAMMA);
    if (!gammaConfig) throw new Error(`No 'Gamma' account configuration`);
    pipeline.addStage(
      new OrcaBusStatefulDeploymentStage(
        this,
        'OrcaBusGamma',
        gammaConfig.stackProps.statefulConfig,
        {
          account: gammaConfig.accountId,
          region: gammaConfig.region,
        }
      ),
      { pre: [new pipelines.ManualApprovalStep('PromoteToGamma')] }
    );

    // Some stack have dependencies to the 'shared stack' so we need to deploy it first beforehand
    // should only be a one-off initial deployment
    //
    // /**
    //  * Deployment to Prod account
    //  */
    // const prodConfig = getEnvironmentConfig(AppStage.PROD);
    // if (!prodConfig) throw new Error(`No 'Prod' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusStatefulDeploymentStage(
    //     this,
    //     'OrcaBusProd',
    //     prodConfig.stackProps.statefulConfig,
    //     {
    //       account: prodConfig.accountId,
    //       region: prodConfig.region,
    //     }
    //   ),
    //   { pre: [new pipelines.ManualApprovalStep('PromoteToProd')] }
    // );

    // need to build pipeline so we could add notification at the pipeline construct
    pipeline.buildPipeline();

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
      notificationRuleName: 'orcabus_stateful_pipeline_notification',
    });
  }
}

class OrcaBusStatefulDeploymentStage extends cdk.Stage {
  constructor(
    scope: Construct,
    environmentName: string,
    statefulStackCollectionProps: StatefulStackCollectionProps,
    env: cdk.Environment
  ) {
    super(scope, environmentName, { env: env });

    new StatefulStackCollection(this, env, statefulStackCollectionProps);
  }
}
