import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { BsshIcav2FastqCopyStateMachineConstruct } from './constructs/bssh-icav2-fastq-copy-manager';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';

export interface BsshIcav2FastqCopyManagerConfig {
  // Define construct properties here
  icav2JwtSecretsManagerPath: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  icav2CopyBatchUtilityStateMachineName: string; // "/icav2/umccr-prod/copy-batch-state-machine/name"
  bsshIcav2FastqCopyManagerStateMachineName: string; // "bssh_icav2_fastq_copy_manager"
  bsshIcav2FastqCopyManagerStateMachineNameSsmParameterPath: string; // "/bssh_icav2_fastq_copy/state_machine/name"
  bsshIcav2FastqCopyManagerStateMachineArnSsmParameterPath: string; // "/bssh_icav2_fastq_copy/state_machine/arn"
  eventBusName: string; // OrcabusMain
}

export type BsshIcav2FastqCopyManagerStackProps = BsshIcav2FastqCopyManagerConfig & cdk.StackProps;

export class BsshIcav2FastqCopyManagerStack extends cdk.Stack {
  public readonly bsshIcav2FastqCopyStateMachineArn: string;

  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyManagerStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine value from lookup
    const icav2_copy_batch_stack_state_machine_arn_obj = sfn.StateMachine.fromStateMachineName(
      this,
      'icav2_copy_batch_state_machine',
      props.icav2CopyBatchUtilityStateMachineName
    );

    // Get the icav2 jwt secret from lookup
    const icav2_jwt_ssm_parameter_obj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'icav2_jwt_secret',
      props.icav2JwtSecretsManagerPath
    );

    // Get the lambda layer object
    const lambda_layer_obj = new PythonLambdaLayerConstruct(this, 'icav2_fastq_copy_lambda_layer', {
      layerName: 'ICAv2FastqCopyManagerLayer',
      layerDescription: 'layer to enable the fastq copy manager tools layer',
      layerDirectory: path.join(__dirname, '../layers'),
    });

    // Get eventbus object
    const event_bus_obj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    const icav2_bclconvert_success_event_state_machine =
      new BsshIcav2FastqCopyStateMachineConstruct(this, id, {
        /* Stack objects */
        icav2CopyBatchStateMachineObj: icav2_copy_batch_stack_state_machine_arn_obj,
        icav2JwtSsmParameterObj: icav2_jwt_ssm_parameter_obj,
        lambdasLayerObj: lambda_layer_obj.lambdaLayerVersionObj,
        eventBusObj: event_bus_obj,
        /* Lambda paths */
        bclconvertSuccessEventHandlerLambdaPath: path.join(
          __dirname,
          '../lambdas/query_bclconvert_outputs_handler'
        ),
        /* State machine paths */
        workflowDefinitionBodyPath: path.join(
          __dirname,
          '../step_functions_templates/bclconvert_success_event_state_machine.json'
        ),
      });

    // Set outputs
    this.bsshIcav2FastqCopyStateMachineArn =
      icav2_bclconvert_success_event_state_machine.icav2BclconvertSuccessEventSsmStateMachineObj.stateMachineArn;

    // Set ssm parameter paths
    new ssm.StringParameter(
      this,
      'bssh_icav2_fastq_copy_manager_state_machine_name_ssm_parameter',
      {
        parameterName: props.bsshIcav2FastqCopyManagerStateMachineNameSsmParameterPath,
        stringValue: props.bsshIcav2FastqCopyManagerStateMachineName,
      }
    );
    new ssm.StringParameter(this, 'bssh_icav2_fastq_copy_manager_state_machine_arn_ssm_parameter', {
      parameterName: props.bsshIcav2FastqCopyManagerStateMachineArnSsmParameterPath,
      stringValue: this.bsshIcav2FastqCopyStateMachineArn,
    });
  }
}
