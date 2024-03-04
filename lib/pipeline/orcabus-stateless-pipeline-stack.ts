import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as iam from 'aws-cdk-lib/aws-iam';
import { OrcaBusStatelessConfig, OrcaBusStatelessStack } from '../workload/orcabus-stateless-stack';
import { getEnvironmentConfig } from '../../config/constants';

export class StatelessPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // A connection where the pipeline get its source code
    const codeStarArn = ssm.StringParameter.valueForStringParameter(this, 'codestar_github_arn');
    const sourceFile = pipelines.CodePipelineSource.connection(
      'umccr/orcabus',
      'fix(postgres-manager)/codebuild-unit-test',
      {
        connectionArn: codeStarArn,
      }
    );

    const unitTest = new pipelines.CodeBuildStep('UnitTest', {
      installCommands: [
        //  RUST installation
        `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y`,
        `source $HOME/.cargo/env`,
      ],
      commands: ['yarn install --immutable', 'make suite'],
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
      commands: ['yarn install --immutable', 'yarn run cdk-stateless-pipeline synth'],
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
    const betaConfig = getEnvironmentConfig('beta');
    if (!betaConfig) throw new Error(`No 'Beta' account configuration`);
    pipeline.addStage(
      new OrcaBusStatelessDeploymentStage(this, 'BetaStatelessDeployment', betaConfig.stackProps, {
        account: betaConfig.accountId,
      })
    );

    // Since the stateless stack might need to reference the stateful resources (e.g. db, sg), we might comment this out
    // to prevent cdk from looking up for non existence resource. Currently the stateful resource is only deployed in
    // dev

    // /**
    //  * Deployment to Gamma (Staging) account
    //  */
    // const gammaConfig = getEnvironmentConfig('gamma');
    // if (!gammaConfig) throw new Error(`No 'Gamma' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusStatelessDeploymentStage(
    //     this,
    //     'GammaStatelessDeployment',
    //     gammaConfig.stackProps,
    //     {
    //       account: gammaConfig.accountId,
    //     }
    //   ),
    //   { pre: [new pipelines.ManualApprovalStep('PromoteToGamma')] }
    // );

    // /**
    //  * Deployment to Prod account
    //  */
    // const prodConfig = getEnvironmentConfig('prod');
    // if (!prodConfig) throw new Error(`No 'Prod' account configuration`);
    // pipeline.addStage(
    //   new OrcaBusStatelessDeploymentStage(this, 'ProdStatelessDeployment', prodConfig.stackProps, {
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
      orcaBusStatelessConfig: OrcaBusStatelessConfig;
    },
    env?: cdk.Environment
  ) {
    super(scope, environmentName, { env: { account: env?.account, region: 'ap-southeast-2' } });

    new OrcaBusStatelessStack(this, 'OrcaBusStatelessStack', stackProps.orcaBusStatelessConfig);
  }
}
