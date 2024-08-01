import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { BsshIcav2FastqCopyStateMachineConstruct } from './constructs/bssh-icav2-fastq-copy-manager';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';
import { ICAv2CopyBatchUtilityConstruct } from '../../../../components/icav2-copy-files-batch';
import { DockerImageCode, DockerImageFunction } from 'aws-cdk-lib/aws-lambda';

export interface BsshIcav2FastqCopyManagerConfig {
  /* Required external properties */
  icav2TokenSecretId: string; // "ICAv2JWTKey-umccr-prod-service-trial"
  /* Event Bus Configurations */
  eventBusName: string; // OrcabusMain
  workflowName: string; // bsshFastqCopy
  workflowVersion: string; // 1.0.0
  serviceVersion: string; // 2024.05.15
  triggerLaunchSource: string; // orcabus.workflowmanager
  internalEventSource: string; // orcabus.bsshFastqCopy
  detailType: string; // WorkflowRunStateChange
}

export type BsshIcav2FastqCopyManagerStackProps = BsshIcav2FastqCopyManagerConfig & cdk.StackProps;

export class BsshIcav2FastqCopyManagerStack extends cdk.Stack {
  public readonly bsshIcav2Map = {
    prefix: 'bsshFastqCopy',
  };

  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyManagerStackProps) {
    super(scope, id, props);

    // Get the icav2 jwt secret from lookup
    const icav2_jwt_secret_obj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'icav2_jwt_secret',
      props.icav2TokenSecretId
    );

    // // Get the lambda layer object
    // const lambda_layer_obj = new PythonLambdaLayerConstruct(this, 'icav2_fastq_copy_lambda_layer', {
    //   layerName: 'ICAv2FastqCopyManagerLayer',
    //   layerDescription: 'layer to enable the fastq copy manager tools layer',
    //   layerDirectory: path.join(__dirname, '../layers'),
    // }).lambdaLayerVersionObj;

    // Get Fastq List Rows lambda
    // const bclconvert_success_event_lambda = new PythonFunction(
    //   this,
    //   'bclconvert_success_event_lambda_python_function',
    //   {
    //     functionName: `${this.bsshIcav2Map.prefix}-bclconvert-success-event-handler`,
    //     entry: path.join(__dirname, '../lambdas/query_bclconvert_outputs_handler_py'),
    //     runtime: lambda.Runtime.PYTHON_3_12,
    //     architecture: lambda.Architecture.ARM_64,
    //     index: 'query_bclconvert_outputs_handler.py',
    //     handler: 'handler',
    //     memorySize: 1024,
    //     layers: [lambda_layer_obj],
    //     timeout: Duration.seconds(60),
    //     environment: {
    //       ICAV2_BASE_URL: 'https://ica.illumina.com/ica/rest',
    //       ICAV2_ACCESS_TOKEN_SECRET_ID: icav2_jwt_secret_obj.secretName,
    //     },
    //   }
    // );

    const bclconvert_success_event_lambda = new DockerImageFunction(
      this,
      'bclconvert_success_event_lambda_python_function',
      {
        functionName: `${this.bsshIcav2Map.prefix}-bclconvert-success-event-handler`,
        code: DockerImageCode.fromImageAsset(path.join(__dirname, '../'), {
          file: 'lambdas/query_bclconvert_outputs_handler_py/Dockerfile',
        }),
      }
    );

    // Get eventbus object
    const event_bus_obj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Construct the icav2 copy files state machines
    const icav2_copy_batch_state_machine_obj = new ICAv2CopyBatchUtilityConstruct(
      this,
      'icav2_copy_batch_state_machine',
      {
        icav2JwtSecretParameterObj: icav2_jwt_secret_obj,
        stateMachineNameSingle: `${this.bsshIcav2Map.prefix}-single-icav2-files-copy`,
        stateMachineNameBatch: `${this.bsshIcav2Map.prefix}-batch-icav2-files-copy`,
      }
    );

    const icav2_bclconvert_success_event_state_machine =
      new BsshIcav2FastqCopyStateMachineConstruct(this, id, {
        /* Metadata */
        prefix: this.bsshIcav2Map.prefix,
        /* Stack objects */
        icav2CopyBatchStateMachineObj: icav2_copy_batch_state_machine_obj.icav2CopyFilesBatchSfnObj,
        icav2JwtSsmParameterObj: icav2_jwt_secret_obj,
        eventBusObj: event_bus_obj,
        /* Lambda paths */
        bclconvertSuccessEventHandlerLambdaObj: bclconvert_success_event_lambda,
        /* State machine paths */
        workflowDefinitionBodyPath: path.join(
          __dirname,
          '../step_functions_templates/bclconvert_success_event_state_machine.json'
        ),
        // Event handling //
        detailType: props.detailType,
        serviceVersion: props.serviceVersion,
        triggerLaunchSource: props.triggerLaunchSource,
        internalEventSource: props.internalEventSource,
        workflowName: props.workflowName,
        workflowVersion: props.workflowVersion,
      });
  }
}
