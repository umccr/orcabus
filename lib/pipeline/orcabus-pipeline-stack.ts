import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import { OrcaBusStatelessConfig, OrcaBusStatelessStack } from '../workload/orcabus-stateless-stack';
import { OrcaBusStatefulConfig, OrcaBusStatefulStack } from '../workload/orcabus-stateful-stack';
import { getEnvironmentConfig } from '../../config/constants';

export class PipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // A connection where the pipeline get its source code
    const codeStarArn = ssm.StringParameter.valueForStringParameter(this, 'codestar_github_arn');
    const sourceFile = pipelines.CodePipelineSource.connection(
      'umccr/orcabus',
      'feature/base-cdk-deployment',
      {
        connectionArn: codeStarArn,
      }
    );

    const orcabusUnitTest = new pipelines.CodeBuildStep('UnitTest', {
      commands: ['yarn install --forzen-lockfile', 'make suite'],
      input: sourceFile,
      primaryOutputDirectory: '.',
    });

    const synthAction = new pipelines.CodeBuildStep('Synth', {
      commands: ['yarn install --frozen-lockfile', 'yarn run cdk synth -v'],
      input: orcabusUnitTest,
      primaryOutputDirectory: 'cdk.out',
    });

    const pipeline = new pipelines.CodePipeline(this, 'Pipeline', {
      synth: synthAction,
      selfMutation: true,
      crossAccountKeys: true,
      dockerEnabledForSynth: true,
      codeBuildDefaults: {
        buildEnvironment: {
          computeType: codebuild.ComputeType.SMALL,
          buildImage: codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
        },
      },
    });

    /**
     * Deployment to Beta (Dev) account
     */
    const betaConfig = getEnvironmentConfig('beta');
    if (!betaConfig) throw new Error(`No 'Beta' account configuration`);
    pipeline.addStage(
      new OrcaBusDeploymentStage(this, 'BetaDeployment', betaConfig.stackProps, {
        account: betaConfig.accountId,
      })
    );

    // /**
    //  * Deployment to Gamma (Staging) account
    //  */
    // const gammaConfig = getEnvironmentConfig('gamma');
    // if (!gammaConfig) throw new Error(`No 'Gamma' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusDeploymentStage(this, 'GammaDeployment', gammaConfig.stackProps, {
    //     account: gammaConfig.accountId,
    //   }),
    //   { pre: [new pipelines.ManualApprovalStep('PromoteToGamma')] }
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

class OrcaBusDeploymentStage extends cdk.Stage {
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

    new OrcaBusStatefulStack(this, 'OrcaBusStatefulStack', stackProps.orcaBusStatefulConfig);
    // new OrcaBusStatelessStack(this, 'OrcaBusStatelessStack', stackProps.orcaBusStatelessConfig);
  }
}
