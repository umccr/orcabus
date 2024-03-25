import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';

interface ICAv2WorkflowSessionStateMachineConstructProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  lambdas_layer_path: string; // __dirname + '/../../../layers
  bclconvert_success_event_handler_path: string; // __dirname + '/../../../lambdas/bclconvert_success_event_handler'
  // execution_check_status_lambda_path: string; // __dirname + '/../../../lambdas/check_execution_completion'
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  icav2_copy_batch_state_machine_arn: string;
  workflow_definition_body_path: string; // __dirname + '/../../../step_functions_templates/bclconvert_success_event_state_machine.json'
}

export class ICAv2WorkflowSessionStateMachineConstruct extends Construct {

  private icav2_jwt_secret_arn_value: string;
  private icav2_jwt_ssm_parameter_path: string;

  public readonly icav2_bclconvert_success_event_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: ICAv2WorkflowSessionStateMachineConstructProps) {
    super(scope, id);

    // Import external ssm parameters
    this.set_jwt_secret_arn_object(props.icav2_jwt_ssm_parameter_path);

    // Set lambda layer arn object
    const lambda_layer = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: props.lambdas_layer_path,
      });

    // Workflow Session lambda
    const bclconvert_success_event_lambda = new PythonFunction(this, 'bclconvert_success_event_lambda_python_function', {
      entry: props.bclconvert_success_event_handler_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [lambda_layer.lambda_layer_version_obj],
      // @ts-ignore
      timeout: Duration.seconds(60),
    });

    // // Copy batch data handler lambda
    // const execution_check_status_lambda_path = new PythonFunction(this, 'check_status_lambda_python_function', {
    //   entry: props.execution_check_status_lambda_path,
    //   runtime: lambda.Runtime.PYTHON_3_11,
    //   index: 'handler.py',
    //   handler: 'handler',
    //   memorySize: 1024,
    //   // This shouldn't go for more than three seconds
    //   // timeout: Duration.seconds(3),
    // });

    // Add icav2 secrets permissions to lambda
    this.add_icav2_secrets_permissions_to_lambda(
      bclconvert_success_event_lambda,
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_list.forEach(
      (ssm_parameter_path) => {
        this.add_get_ssm_parameter_permission_to_lambda_role_policy(
          bclconvert_success_event_lambda,
          ssm_parameter_path,
        );
      },
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'bclconvert_success_event_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflow_definition_body_path),
      // definitionSubstitutions
      definitionSubstitutions: {
        '__bclconvert_success_event_lambda_arn__': bclconvert_success_event_lambda.functionArn,
        '__copy_batch_data_state_machine_arn__': props.icav2_copy_batch_state_machine_arn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            bclconvert_success_event_lambda.functionArn
          ],
          actions: [
            'lambda:InvokeFunction',
          ],
        },
      ),
    );


    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachine.addToRolePolicy(
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

    // Add state machine execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            props.icav2_copy_batch_state_machine_arn,
          ],
          actions: [
            'states:StartExecution',
          ],
        },
      ),
    );

    // // Allow statemachine execution check access to describe the copy batch state machine execution
    // execution_check_status_lambda_path.addToRolePolicy(
    //   // @ts-ignore
    //   new iam.PolicyStatement(
    //     {
    //       resources: [
    //         props.icav2_copy_batch_state_machine_arn,
    //       ],
    //       actions: [
    //         'states:DescribeExecution',
    //       ],
    //     },
    //   ),
    // );

    // Set outputs
    this.icav2_bclconvert_success_event_state_machine_arn = stateMachine.stateMachineArn;

  }

  private set_jwt_secret_arn_object(icav2_jwt_ssm_parameter_path: string) {
    const icav2_jwt_ssm_parameter = ssm.StringParameter.fromStringParameterName(
      this,
      'get_jwt_secret_arn_value',
      icav2_jwt_ssm_parameter_path,
    );

    this.icav2_jwt_ssm_parameter_path = icav2_jwt_ssm_parameter.parameterArn;
    this.icav2_jwt_secret_arn_value = icav2_jwt_ssm_parameter.stringValue;
  }

  private add_icav2_secrets_permissions_to_lambda(
    lambda_function: lambda.Function | PythonFunction,
  ) {
    /*
    Add the statement that allows
    */
    lambda_function.addToRolePolicy(
      // @ts-ignore
      new iam.PolicyStatement(
        {
          resources: [
            this.icav2_jwt_secret_arn_value,
            this.icav2_jwt_ssm_parameter_path,
          ],
          actions: [
            'secretsmanager:GetSecretValue',
            'ssm:GetParameter',
          ],
        },
      ),
    );
  }

  private add_get_ssm_parameter_permission_to_lambda_role_policy(
    lambda_function: lambda.Function | PythonFunction, ssm_parameter_path: string,
  ) {
    lambda_function.addToRolePolicy(
      // @ts-ignore
      new iam.PolicyStatement(
        {
          resources: [
            `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter${ssm_parameter_path}`,
          ],
          actions: [
            'ssm:GetParameter',
          ],
        },
      ),
    );
  }

}
