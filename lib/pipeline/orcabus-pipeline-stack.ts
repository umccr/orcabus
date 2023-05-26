import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as pipelines from 'aws-cdk-lib/pipelines';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
// import { OrcaBusStatelessStack } from '../workload/orcabus-stateless-stack';
import { OrcaBusStatefulStack } from '../workload/orcabus-stateful-stack';
import {
  getEnvironmentConfig,
  orcaBusStatefulConfig,
  orcaBusStatelessConfig,
} from '../../config/constants';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';

export class PipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    // A connection where the pipeline get its source code
    const codeStarArn = ssm.StringParameter.valueForStringParameter(this, 'codestar_github_arn');

    const synthAction = new pipelines.CodeBuildStep('Synth', {
      // TODO: Change branch
      input: pipelines.CodePipelineSource.connection('umccr/orcabus', 'cdk-pipeline', {
        connectionArn: codeStarArn,
      }),
      commands: ['yarn install --frozen-lockfile', 'make build', 'yarn cdk synth -v'],
      primaryOutputDirectory: 'cdk.out',
      env: {},
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
      selfMutation: false, //TODO: Remove this
      codeBuildDefaults: {
        buildEnvironment: {
          buildImage: codebuild.LinuxBuildImage.STANDARD_6_0,
        },
      },
      dockerEnabledForSelfMutation: true,
    });

    const betaStage = new OrcaBusDeploymentStage(this, 'BetaDeployment', {
      account: getEnvironmentConfig('beta')?.accountId,
    });

    pipeline.addStage(betaStage);
  }
}

class OrcaBusDeploymentStage extends cdk.Stage {
  constructor(scope: Construct, environmentName: string, env?: cdk.Environment) {
    super(scope, environmentName, { env: { account: env?.account, region: 'ap-southeast-2' } });

    new OrcaBusStatefulStack(this, 'OrcaBusStatefulStack', orcaBusStatefulConfig);
    // new OrcaBusStatelessStack(this, 'OrcaBusStatelessStack', orcaBusStatelessConfig);
  }
}
