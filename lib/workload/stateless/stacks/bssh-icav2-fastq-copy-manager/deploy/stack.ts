import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { BsshIcav2FastqCopyStateMachineConstruct } from './constructs/bssh-icav2-fastq-copy-manager';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';

export interface BsshIcav2FastqCopyManagerConfig {
  // Define construct properties here
  icav2_jwt_secrets_manager_path: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  icav2_copy_batch_utility_state_machine_name: string; // "/icav2/umccr-prod/copy-batch-state-machine/name"
  bssh_icav2_fastq_copy_manager_state_machine_name: string; // "bssh_icav2_fastq_copy_manager"
  bssh_icav2_fastq_copy_manager_state_machine_name_ssm_parameter_path: string; // "/bssh_icav2_fastq_copy/state_machine/name"
  bssh_icav2_fastq_copy_manager_state_machine_arn_ssm_parameter_path: string; // "/bssh_icav2_fastq_copy/state_machine/arn"
}

export type BsshIcav2FastqCopyManagerStackProps = BsshIcav2FastqCopyManagerConfig & cdk.StackProps;

export class BsshIcav2FastqCopyManagerStack extends cdk.Stack {
  public readonly bssh_icav2_fastq_copy_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyManagerStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine value from lookup
    const icav2_copy_batch_stack_state_machine_arn_obj = sfn.StateMachine.fromStateMachineName(
      this,
      'icav2_copy_batch_state_machine',
      props.icav2_copy_batch_utility_state_machine_name
    );

    // Get the icav2 jwt secret from lookup
    const icav2_jwt_ssm_parameter_obj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'icav2_jwt_ssm_parameter',
      props.icav2_jwt_secrets_manager_path
    );

    // Get the lambda layer object
    const lambda_layer_obj = new PythonLambdaLayerConstruct(this, 'icav2_fastq_copy_lambda_layer', {
      layer_name: 'ICAv2FastqCopyManagerLayer',
      layer_description: 'layer to enable the fastq copy manager tools layer',
      layer_directory: path.join(__dirname, '../layers'),
    });

    const icav2_bclconvert_success_event_state_machine =
      new BsshIcav2FastqCopyStateMachineConstruct(this, id, {
        /* Stack objects */
        icav2_copy_batch_state_machine_obj: icav2_copy_batch_stack_state_machine_arn_obj,
        icav2_jwt_ssm_parameter_obj: icav2_jwt_ssm_parameter_obj,
        lambdas_layer_obj: lambda_layer_obj.lambda_layer_version_obj,
        /* Lambda paths */
        bclconvert_success_event_handler_lambda_path: path.join(
          __dirname,
          '../lambdas/query_bclconvert_outputs_handler'
        ),
        /* State machine paths */
        workflow_definition_body_path: path.join(
          __dirname,
          '../step_functions_templates/bclconvert_success_event_state_machine.json'
        ),
      });

    // Set outputs
    this.bssh_icav2_fastq_copy_state_machine_arn =
      icav2_bclconvert_success_event_state_machine.icav2_bclconvert_success_event_ssm_state_machine_obj.stateMachineArn;

    // Set ssm parameter paths
    new ssm.StringParameter(
      this,
      'bssh_icav2_fastq_copy_manager_state_machine_name_ssm_parameter',
      {
        parameterName: props.bssh_icav2_fastq_copy_manager_state_machine_name_ssm_parameter_path,
        stringValue: props.bssh_icav2_fastq_copy_manager_state_machine_name,
      }
    );
    new ssm.StringParameter(this, 'bssh_icav2_fastq_copy_manager_state_machine_arn_ssm_parameter', {
      parameterName: props.bssh_icav2_fastq_copy_manager_state_machine_arn_ssm_parameter_path,
      stringValue: this.bssh_icav2_fastq_copy_state_machine_arn,
    });
  }
}
