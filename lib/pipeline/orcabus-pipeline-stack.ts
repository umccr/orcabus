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
    const sourceFile = pipelines.CodePipelineSource.connection('umccr/orcabus', 'main', {
      connectionArn: codeStarArn,
    });

    const synthAction = new pipelines.CodeBuildStep('Synth', {
      input: sourceFile,
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
    synthAction.addStepDependency(new OrcaBusTestStep('OrcaBusUnitTest', { source: sourceFile }));

    const pipeline = new pipelines.CodePipeline(this, 'Pipeline', {
      synth: synthAction,
      selfMutation: true,
      crossAccountKeys: true,
      codeBuildDefaults: {
        buildEnvironment: {
          buildImage: codebuild.LinuxBuildImage.STANDARD_6_0,
        },
      },
      dockerEnabledForSelfMutation: true,
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

    /**
     * Deployment to Gamma (Staging) account
     */
    const gammaConfig = getEnvironmentConfig('gamma');
    if (!gammaConfig) throw new Error(`No 'Gamma' account configuration`);
    pipeline.addStage(
      new OrcaBusDeploymentStage(this, 'GammaDeployment', gammaConfig.stackProps, {
        account: gammaConfig.accountId,
      }),
      { pre: [new pipelines.ManualApprovalStep('PromoteToGamma')] }
    );

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
    new OrcaBusStatelessStack(this, 'OrcaBusStatelessStack', stackProps.orcaBusStatelessConfig);
  }
}

interface OrcaBusTestStepProps {
  source: pipelines.CodePipelineSource;
}
class OrcaBusTestStep extends pipelines.CodeBuildStep {
  constructor(id: string, props: OrcaBusTestStepProps) {
    const stepProps: pipelines.CodeBuildStepProps = {
      input: props.source,
      commands: [],
      partialBuildSpec: codebuild.BuildSpec.fromObject({
        env: {
          shell: 'bash',
        },
        phases: {
          install: {
            commands: [
              'wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py310_23.3.1-0-Linux-x86_64.sh',
              'bash Miniconda3-py310_23.3.1-0-Linux-x86_64.sh -b',
              'export PATH=/root/miniconda3/bin:$PATH',
              'conda init bash',
              'source activate',
              'conda create -q -n orcabus python=3.10',
              'conda run -n orcabus yarn install',
            ],
          },
          build: {
            commands: ['conda run -n orcabus make test'],
          },
        },
        version: '0.2',
      }),
    };
    super(id, stepProps);
  }
}
