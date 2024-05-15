import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { BsshIcav2FastqCopyStateMachineConstruct } from './constructs/bssh-icav2-fastq-copy-manager';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import { ICAv2CopyBatchUtilityConstruct } from '../../../../components/icav2-copy-files-batch';

export interface BsshIcav2FastqCopyManagerConfig {
  /* Required external properties */
  icav2TokenSecretId: string; // "ICAv2JWTKey-umccr-prod-service-trial"

  /* Configurables for this stack */
  // The name of this AWS Step function state machine
  bsshIcav2FastqCopyManagerStateMachinePrefix: string; // "bssh_icav2_fastq_copy_manager"

  /* Events Handling */
  eventBusName: string; // OrcabusMain
  workflowType: string; // bssh_fastq_copy
  workflowVersion: string; // 1.0.0
  serviceVersion: string; // 2024.05.15
  triggerLaunchSource: string; // orcabus.wfm
  internalEventSource: string; // orcabus.bssh_fastq_copy
  detailType: string; // workflowRunStateChange
}

export type BsshIcav2FastqCopyManagerStackProps = BsshIcav2FastqCopyManagerConfig & cdk.StackProps;

export class BsshIcav2FastqCopyManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyManagerStackProps) {
    super(scope, id, props);

    // Get the icav2 jwt secret from lookup
    const icav2_jwt_secret_obj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'icav2_jwt_secret',
      props.icav2TokenSecretId
    );

    // Get the lambda layer object
    const lambda_layer_obj = new PythonLambdaLayerConstruct(this, 'icav2_fastq_copy_lambda_layer', {
      layerName: 'ICAv2FastqCopyManagerLayer',
      layerDescription: 'layer to enable the fastq copy manager tools layer',
      layerDirectory: path.join(__dirname, '../layers'),
    });

    // Get eventbus object
    const event_bus_obj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Construct the icav2 copy files state machines
    const icav2_copy_batch_state_machine = new ICAv2CopyBatchUtilityConstruct(
      this,
      'icav2_copy_batch_state_machine',
      {
        icav2JwtSecretParameterObj: icav2_jwt_secret_obj,
        stateMachineNameSingle: `${props.bsshIcav2FastqCopyManagerStateMachinePrefix}-single-icav2-files-copy`,
        stateMachineNameBatch: `${props.bsshIcav2FastqCopyManagerStateMachinePrefix}-batch-icav2-files-copy`,
      }
    );

    const icav2_bclconvert_success_event_state_machine =
      new BsshIcav2FastqCopyStateMachineConstruct(this, id, {
        /* Stack objects */
        icav2CopyBatchStateMachineObj: icav2_copy_batch_state_machine.icav2CopyFilesBatchSfnObj,
        icav2JwtSecretObj: icav2_jwt_secret_obj,
        lambdasLayerObj: lambda_layer_obj.lambdaLayerVersionObj,
        eventBusObj: event_bus_obj,
        /* Lambda paths */
        bclconvertSuccessEventHandlerLambdaPath: path.join(
          __dirname,
          '../lambdas/query_bclconvert_outputs_handler'
        ),
        /* State machine */
        stateMachineName: props.bsshIcav2FastqCopyManagerStateMachinePrefix,
        workflowDefinitionBodyPath: path.join(
          __dirname,
          '../step_functions_templates/bclconvert_success_event_state_machine.json'
        ),
        // Event handling //
        detailType: props.detailType,
        serviceVersion: props.serviceVersion,
        triggerLaunchSource: props.triggerLaunchSource,
        internalEventSource: props.internalEventSource,
        workflowType: props.workflowType,
        workflowVersion: props.workflowVersion,
      });
  }
}
