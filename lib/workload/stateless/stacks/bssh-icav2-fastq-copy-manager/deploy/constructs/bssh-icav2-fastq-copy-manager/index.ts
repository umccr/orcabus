import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

interface BsshIcav2FastqCopyStateMachineConstructProps {
  icav2_copy_batch_state_machine_obj: sfn.IStateMachine;
  icav2_jwt_ssm_parameter_obj: secretsmanager.ISecret;
  lambdas_layer_obj: lambda.ILayerVersion;
  bclconvert_success_event_handler_lambda_path: string; // __dirname + '/../../../lambdas/bclconvert_success_event_handler'
  // execution_check_status_lambda_path: string; // __dirname + '../lambdas/check_execution_completion'
  workflow_definition_body_path: string; // __dirname + '../step_functions_templates/bclconvert_success_event_state_machine.json'
}

export class BsshIcav2FastqCopyStateMachineConstruct extends Construct {
  public readonly icav2_bclconvert_success_event_ssm_state_machine_obj: sfn.IStateMachine;

  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyStateMachineConstructProps) {
    super(scope, id);

    // Workflow Session lambda
    const bclconvert_success_event_lambda = new PythonFunction(
      this,
      'bclconvert_success_event_lambda_python_function',
      {
        entry: props.bclconvert_success_event_handler_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdas_layer_obj],
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_BASE_URL: 'https://ica.illumina.com/ica/rest',
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2_jwt_ssm_parameter_obj.secretName,
        },
      }
    );

    // Add icav2 secrets permissions to lambda
    props.icav2_jwt_ssm_parameter_obj.grantRead(<iam.IRole>bclconvert_success_event_lambda.role);

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'bssh_fastq_copy_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflow_definition_body_path),
      // definitionSubstitutions
      definitionSubstitutions: {
        __bclconvert_success_event_lambda_arn__: bclconvert_success_event_lambda.functionArn,
        __copy_batch_data_state_machine_arn__:
          props.icav2_copy_batch_state_machine_obj.stateMachineArn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [bclconvert_success_event_lambda.functionArn],
        actions: ['lambda:InvokeFunction'],
      })
    );

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Allow the icav2 copy batch statemachine to be started by the bssh fastq copy manager
    // State machine
    props.icav2_copy_batch_state_machine_obj.grantStartExecution(stateMachine.role);

    // Set outputs
    this.icav2_bclconvert_success_event_ssm_state_machine_obj = stateMachine;
  }
}
