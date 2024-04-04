import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';


export interface ICAv2CopyBatchUtilityConstructProps {
  /* Constructs */
  icav2_jwt_secret_parameter_obj: secretsManager.ISecret;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  lambdas_layer: LambdaLayerConstruct; // __dirname + '/../../../layers'
  /* Paths */
  manifest_handler_lambda_path: string; // __dirname + '/../../../lambdas/manifest_handler'
  check_or_launch_job_lambda_path: string; // __dirname + '/../../../lambdas/check_or_launch_job'
  /* StateMachine paths */
  state_machine_batch_definition_body_path: string; // __dirname + '/../../../step_functions_templates/copy_batch_state_machine.json'
  state_machine_single_definition_body_path: string; // __dirname + '/../../../step_functions_templates/copy_single_state_machine.json'
}

export class ICAv2CopyBatchUtilityConstruct extends Construct {

  public readonly icav2_copy_batch_state_machine: sfn.StateMachine;
  public readonly icav2_copy_single_state_machine: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: ICAv2CopyBatchUtilityConstructProps) {
    super(scope, id);

    // Manifest inverter lambda
    const manifest_inverter_lambda = new PythonFunction(this, 'manifest_inverter_lambda', {
      entry: props.manifest_handler_lambda_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [props.lambdas_layer.lambda_layer_version_obj]
    });

    // Job Status Handler
    const check_or_launch_job_lambda = new PythonFunction(this, 'check_or_launch_job_lambda', {
      entry: props.check_or_launch_job_lambda_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [props.lambdas_layer.lambda_layer_version_obj],
      // @ts-ignore // We go through at least 10 jobs now to check if they're completed
      timeout: Duration.seconds(300),
      environment: {
        "ICAV2_ACCESS_TOKEN_SECRET_ID": props.icav2_jwt_secret_parameter_obj.secretName
      },
    });

    // Specify the single statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachineSingle = new sfn.StateMachine(this, 'copy_single_state_machine', {
      // Name
      stateMachineName: 'copy_single_state_machine',
      // Definition Template
      definitionBody: DefinitionBody.fromFile(props.state_machine_single_definition_body_path),
      // Definition Substitutions
      definitionSubstitutions: {
        '__check_or_launch_job_lambda_arn__': check_or_launch_job_lambda.functionArn,
      },
    });

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachineBatch = new sfn.StateMachine(this, 'copy_batch_state_machine', {
      stateMachineName: 'copy_batch_state_machine',
      // Definition Template
      definitionBody: DefinitionBody.fromFile(props.state_machine_batch_definition_body_path),
      // Definition Substitutions
      definitionSubstitutions: {
        '__manifest_inverter_lambda_arn__': manifest_inverter_lambda.functionArn,
        '__copy_single_job_state_machine_arn__': stateMachineSingle.stateMachineArn,
      },
    });

    // Add execution permissions to stateMachine role
    manifest_inverter_lambda.grantInvoke(
      // @ts-ignore
      <iam.IRole>stateMachineBatch.role
    )

    // Add execution permissions to stateMachine role
    check_or_launch_job_lambda.grantInvoke(
      // @ts-ignore
      <iam.IRole>stateMachineSingle.role
    )

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachineBatch.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
          ],
          actions: [
            'events:PutTargets',
            'events:PutRule',
            'events:DescribeRule',
          ],
        },
      ),
    );

    // Add state machine execution permissions to stateMachineBatch role
    stateMachineSingle.grantStartExecution(
      stateMachineBatch.role
    )

    // Update lambda policies
    props.icav2_jwt_secret_parameter_obj.grantRead(
      // @ts-ignore
      check_or_launch_job_lambda.role
    );


    // Set outputs
    this.icav2_copy_batch_state_machine = stateMachineBatch;
    this.icav2_copy_single_state_machine = stateMachineSingle;
  }


}

