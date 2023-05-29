import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import { OrcaBusStatelessConfig, OrcaBusStatelessStack } from '../workload/orcabus-stateless-stack';
import { OrcaBusStatefulConfig, OrcaBusStatefulStack } from '../workload/orcabus-stateful-stack';
import { getEnvironmentConfig } from '../../config/constants';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';

export class PipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // A connection where the pipeline get its source code
    const codeStarArn = ssm.StringParameter.valueForStringParameter(this, 'codestar_github_arn');

    const synthAction = new pipelines.CodeBuildStep('Synth', {
      input: pipelines.CodePipelineSource.connection('umccr/orcabus', 'main', {
        connectionArn: codeStarArn,
      }),
      commands: ['yarn install --frozen-lockfile', 'make build', 'yarn cdk synth -v'],
      primaryOutputDirectory: 'cdk.out',
      rolePolicyStatements: [
        new PolicyStatement({
          actions: ['sts:AssumeRole'],
          resources: ['*'],
          conditions: {
            StringEquals: {
              'iam:ResourceTag/aws-cdk:bootstrap-role': 'lookup',
            },
          },
        }),
      ],
    });

    const pipeline = new pipelines.CodePipeline(this, 'Pipeline', {
      synth: synthAction,
      crossAccountKeys: true,
      codeBuildDefaults: {
        buildEnvironment: {
          buildImage: codebuild.LinuxBuildImage.STANDARD_6_0,
        },
      },
      dockerEnabledForSelfMutation: true,
    });

    const betaConfig = getEnvironmentConfig('beta');
    if (betaConfig) {
      pipeline.addStage(
        new OrcaBusDeploymentStage(this, 'BetaDeployment', betaConfig.stackProps, {
          account: getEnvironmentConfig('beta')?.accountId,
        })
      );
    }

    const gammaConfig = getEnvironmentConfig('gamma');
    if (gammaConfig) {
      pipeline.addStage(
        new OrcaBusDeploymentStage(this, 'GammaDeployment', gammaConfig.stackProps, {
          account: gammaConfig?.accountId,
        }),
        { pre: [new pipelines.ManualApprovalStep('PromoteToGamma')] }
      );
    }

    // TODO: Enable if it is ready for deployment
    // const prodConfig = getEnvironmentConfig('prod');
    // if (prodConfig) {
    //   pipeline.addStage(
    //     new OrcaBusDeploymentStage(this, 'prodDeployment', prodConfig.stackProps, {
    //       account: gammaConfig?.accountId,
    //     }),
    //     { pre: [new pipelines.ManualApprovalStep('PromoteToProd')] }
    //   );
    // }
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
    new OrcaBusStatelessStack(this, 'OrcaBusStatelessStack', stackProps.orcaBusStatelessConfig);
  }
}
