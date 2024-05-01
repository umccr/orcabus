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
  Icav2JwtSecretsManagerPath: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  Icav2CopyBatchUtilityStateMachineName: string; // "/icav2/umccr-prod/copy-batch-state-machine/name"
  BsshIcav2FastqCopyManagerStateMachineName: string; // "bssh_icav2_fastq_copy_manager"
  BsshIcav2FastqCopyManagerStateMachineNameSsmParameterPath: string; // "/bssh_icav2_fastq_copy/state_machine/name"
  BsshIcav2FastqCopyManagerStateMachineArnSsmParameterPath: string; // "/bssh_icav2_fastq_copy/state_machine/arn"
}

export type BsshIcav2FastqCopyManagerStackProps = BsshIcav2FastqCopyManagerConfig & cdk.StackProps;

export class BsshIcav2FastqCopyManagerStack extends cdk.Stack {
  public readonly BsshIcav2FastqCopyStateMachineArn: string;

  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyManagerStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine value from lookup
    const icav2_copy_batch_stack_state_machine_arn_obj = sfn.StateMachine.fromStateMachineName(
      this,
      'icav2_copy_batch_state_machine',
      props.Icav2CopyBatchUtilityStateMachineName
    );

    // Get the icav2 jwt secret from lookup
    const icav2_jwt_ssm_parameter_obj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'icav2_jwt_secret',
      props.Icav2JwtSecretsManagerPath
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
        lambdas_layer_obj: lambda_layer_obj.lambdaLayerVersionObj,
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
    this.BsshIcav2FastqCopyStateMachineArn =
      icav2_bclconvert_success_event_state_machine.icav2_bclconvert_success_event_ssm_state_machine_obj.stateMachineArn;

    // Set ssm parameter paths
    new ssm.StringParameter(
      this,
      'bssh_icav2_fastq_copy_manager_state_machine_name_ssm_parameter',
      {
        parameterName: props.BsshIcav2FastqCopyManagerStateMachineNameSsmParameterPath,
        stringValue: props.BsshIcav2FastqCopyManagerStateMachineName,
      }
    );
    new ssm.StringParameter(this, 'bssh_icav2_fastq_copy_manager_state_machine_arn_ssm_parameter', {
      parameterName: props.BsshIcav2FastqCopyManagerStateMachineArnSsmParameterPath,
      stringValue: this.BsshIcav2FastqCopyStateMachineArn,
    });
  }
}
