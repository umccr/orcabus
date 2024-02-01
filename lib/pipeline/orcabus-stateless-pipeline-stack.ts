import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as iam from 'aws-cdk-lib/aws-iam';
import { OrcaBusStatelessConfig, OrcaBusStatelessStack } from '../workload/orcabus-stateless-stack';
import { OrcaBusStatefulConfig } from '../workload/orcabus-stateful-stack';
import { getEnvironmentConfig } from '../../config/constants';

export class StatelessPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // A connection where the pipeline get its source code
    const codeStarArn = ssm.StringParameter.valueForStringParameter(this, 'codestar_github_arn');
    const sourceFile = pipelines.CodePipelineSource.connection(
      'umccr/orcabus',
      'feature/base-cdk-codepipeline',
      {
        connectionArn: codeStarArn,
      }
    );

    const synthAction = new pipelines.CodeBuildStep('Synth', {
      commands: ['yarn install --frozen-lockfile', 'make suite', 'yarn run cdk synth'],
      input: sourceFile,
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
    const betaConfig = getEnvironmentConfig('beta');
    if (!betaConfig) throw new Error(`No 'Beta' account configuration`);
    pipeline.addStage(
      new OrcaBusStatelessDeploymentStage(this, 'BetaDeployment', betaConfig.stackProps, {
        account: betaConfig.accountId,
      }),
      {
        pre: [
          // need to make sure state*ful* stack matches with the current asset
          new pipelines.CodeBuildStep('BetaStatefulDiffCheck', {
            commands: [
              'yarn install --frozen-lockfile',
              "yarn run cdk diff -a 'yarn run ts-node --prefer-ts-exts bin/orcabus.ts' --fail OrcaBusStatefulStack",
            ],
            rolePolicyStatements: [
              new iam.PolicyStatement({
                effect: iam.Effect.ALLOW,
                actions: ['sts:AssumeRole'],
                resources: ['*'],
              }),
            ],
            buildEnvironment: {
              environmentVariables: {
                CDK_DEPLOY_ACCOUNT: {
                  value: betaConfig.accountId,
                },
              },
            },
          }),
        ],
      }
    );

    // /**
    //  * Deployment to Gamma (Staging) account
    //  */
    // const gammaConfig = getEnvironmentConfig('gamma');
    // if (!gammaConfig) throw new Error(`No 'Gamma' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusStatelessDeploymentStage(this, 'GammaDeployment', gammaConfig.stackProps, {
    //     account: gammaConfig.accountId,
    //   }),
    //   {
    //     pre: [
    //       // need to make sure stateful stack matches
    //       // new pipelines.CodeBuildStep('StatefulDiffCheck', {
    //       //   commands: [
    //       //     'yarn install --frozen-lockfile',
    //       //     'yarn run cdk diff OrcaBusPipeline/GammaDeployment/OrcaBusStatelessStack --fail',
    //       //   ],
    //       // }),
    //       // approval to gamma release
    //       new pipelines.ManualApprovalStep('PromoteToGamma'),
    //     ],
    //   }
    // );

    /**
     * Deployment to Prod account (DISABLED)
     */
    // const prodConfig = getEnvironmentConfig('prod');
    // if (!prodConfig) throw new Error(`No 'Prod' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusDeploymentStage(this, 'prodDeployment', prodConfig.stackProps, {
    //     account: gammaConfig?.accountId,
    //   }),
    //   { pre: [new pipelines.ManualApprovalStep('PromoteToProd')] }
    // );
  }
}

class OrcaBusStatelessDeploymentStage extends cdk.Stage {
  constructor(
    scope: Construct,
    environmentName: string,
    stackProps: {
      orcaBusStatefulConfig: OrcaBusStatefulConfig;
      orcaBusStatelessConfig: OrcaBusStatelessConfig;
    },
    env?: cdk.Environment
  ) {
    super(scope, environmentName, { env: { account: env?.account, region: 'ap-southeast-2' } });

    new OrcaBusStatelessStack(this, 'OrcaBusStatelessStack', stackProps.orcaBusStatelessConfig);
  }
}
