import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { PythonLambdaLayerConstruct } from '../../../../../../components/python-lambda-layer';

export interface ICAv2CopyBatchUtilityConstructProps {
  /* Constructs */
  icav2JwtSecretParameterObj: secretsManager.ISecret; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  lambdasLayer: PythonLambdaLayerConstruct; // __dirname + '/../../../layers'
  /* Paths */
  manifestHandlerLambdaPath: string; // __dirname + '/../../../lambdas/manifest_handler'
  checkOrLaunchJobLambdaPath: string; // __dirname + '/../../../lambdas/check_or_launch_job'
  /* StateMachine paths */
  stateMachineNameSingle: string; // 'copy_single_state_machine'
  stateMachineNameBatch: string; // 'copy_batch_state_machine'
  stateMachineBatchDefinitionBodyPath: string; // __dirname + '/../../../step_functions_templates/copy_batch_state_machine.asl.json'
  stateMachineSingleDefinitionBodyPath: string; // __dirname + '/../../../step_functions_templates/copy_single_state_machine.json'
}

export class ICAv2CopyBatchUtilityConstruct extends Construct {
  public readonly icav2CopyBatchStateMachine: sfn.StateMachine;
  public readonly icav2CopySingleStateMachine: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: ICAv2CopyBatchUtilityConstructProps) {
    super(scope, id);

    // Manifest inverter lambda
    const manifest_inverter_lambda = new PythonFunction(this, 'manifest_inverter_lambda', {
      entry: props.manifestHandlerLambdaPath,
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      layers: [props.lambdasLayer.lambdaLayerVersionObj],
    });

    // Job Status Handler
    const check_or_launch_job_lambda = new PythonFunction(this, 'check_or_launch_job_lambda', {
      entry: props.checkOrLaunchJobLambdaPath,
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      layers: [props.lambdasLayer.lambdaLayerVersionObj],
      timeout: Duration.seconds(300),
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2JwtSecretParameterObj.secretName,
      },
    });

    // Specify the single statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachineSingle = new sfn.StateMachine(this, 'copy_single_state_machine', {
      // Name
      stateMachineName: props.stateMachineNameSingle,
      // Definition Template
      definitionBody: DefinitionBody.fromFile(props.stateMachineSingleDefinitionBodyPath),
      // Definition Substitutions
      definitionSubstitutions: {
        __check_or_launch_job_lambda_arn__: check_or_launch_job_lambda.functionArn,
      },
    });

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachineBatch = new sfn.StateMachine(this, 'copy_batch_state_machine', {
      stateMachineName: props.stateMachineNameBatch,
      // Definition Template
      definitionBody: DefinitionBody.fromFile(props.stateMachineBatchDefinitionBodyPath),
      // Definition Substitutions
      definitionSubstitutions: {
        __manifest_inverter_lambda_arn__: manifest_inverter_lambda.functionArn,
        __copy_single_job_state_machine_arn__: stateMachineSingle.stateMachineArn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachineBatch.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [manifest_inverter_lambda.functionArn],
        actions: ['lambda:InvokeFunction'],
      })
    );

    // Add execution permissions to stateMachine role
    stateMachineSingle.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [check_or_launch_job_lambda.functionArn],
        actions: ['lambda:InvokeFunction'],
      })
    );

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachineBatch.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Add state machine execution permissions to stateMachineBatch role
    stateMachineSingle.grantStartExecution(stateMachineBatch.role);

    // Update lambda policies
    props.icav2JwtSecretParameterObj.grantRead(<iam.IRole>check_or_launch_job_lambda.role);

    // Set outputs
    this.icav2CopyBatchStateMachine = stateMachineBatch;
    this.icav2CopySingleStateMachine = stateMachineSingle;
  }
}
