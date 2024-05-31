import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { ICAv2CopyFilesConstruct } from '../icav2-copy-files';

export interface ICAv2CopyFilesBatchConstructProps {
  /* Constructs */
  icav2JwtSecretParameterObj: secretsManager.ISecret; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  /* StateMachine paths */
  stateMachineNameSingle: string; // 'copy_single_state_machine'
  stateMachineNameBatch: string; // 'copy_batch_state_machine'
}

export class ICAv2CopyBatchUtilityConstruct extends Construct {
  public readonly icav2CopyFilesSfnObj: sfn.StateMachine;
  public readonly icav2CopyFilesBatchSfnObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: ICAv2CopyFilesBatchConstructProps) {
    super(scope, id);

    // Manifest inverter lambda
    const manifest_inverter_lambda = new PythonFunction(this, 'manifest_inverter_lambda', {
      entry: path.join(__dirname, 'manifest_handler_lambda_py'),
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      index: 'manifest_handler_lambda.py',
      handler: 'handler',
      memorySize: 1024,
    });

    // Generate the single state machine
    this.icav2CopyFilesSfnObj = new ICAv2CopyFilesConstruct(this, 'icav2_copy_files_sfn', {
      icav2JwtSecretParameterObj: props.icav2JwtSecretParameterObj,
      stateMachineName: props.stateMachineNameSingle,
    }).icav2CopyFilesSfnObj;

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    this.icav2CopyFilesBatchSfnObj = new sfn.StateMachine(this, 'icav2_copy_files_batch_sfn', {
      stateMachineName: props.stateMachineNameBatch,
      // Definition Template
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_functions_templates/copy_files_batch_sfn.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        __manifest_inverter_lambda_arn__: manifest_inverter_lambda.currentVersion.functionArn,
        __copy_single_job_state_machine_arn__: this.icav2CopyFilesSfnObj.stateMachineArn,
      },
    });

    // Add execution permissions to stateMachine role
    manifest_inverter_lambda.currentVersion.grantInvoke(this.icav2CopyFilesBatchSfnObj.role);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    this.icav2CopyFilesBatchSfnObj.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Add state machine execution permissions to stateMachineBatch role
    this.icav2CopyFilesSfnObj.grantStartExecution(this.icav2CopyFilesBatchSfnObj.role);
  }
}
