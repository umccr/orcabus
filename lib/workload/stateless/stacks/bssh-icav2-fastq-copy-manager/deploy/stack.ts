import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { BsshIcav2FastqCopyStateMachineConstruct } from './constructs/bssh-icav2-fastq-copy-manager';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import {PythonFunction} from "@aws-cdk/aws-lambda-python-alpha";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {Duration} from "aws-cdk-lib";

export interface BsshIcav2FastqCopyManagerConfig {
  // Define construct properties here
  icav2JwtSecretsManagerPath: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  icav2CopyBatchUtilityStateMachineName: string; // "/icav2/umccr-prod/copy-batch-state-machine/name"
  eventBusName: string; // OrcabusMain
}

export type BsshIcav2FastqCopyManagerStackProps = BsshIcav2FastqCopyManagerConfig & cdk.StackProps;

export class BsshIcav2FastqCopyManagerStack extends cdk.Stack {
  public readonly bsshIcav2Map = {
      prefix: "bsshFastqCopy"
  }

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
    }).lambdaLayerVersionObj;

    // Get Fastq List Rows lambda
    const bclconvert_success_event_lambda = new PythonFunction(
      this,
      'bclconvert_success_event_lambda_python_function',
      {
        functionName: `${this.bsshIcav2Map.prefix}-bclconvert-success-event-handler`,
        entry: path.join(
          __dirname,
          '../lambdas/query_bclconvert_outputs_handler_py'
        ),
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'query_bclconvert_outputs_handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [lambda_layer_obj],
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_BASE_URL: 'https://ica.illumina.com/ica/rest',
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2_jwt_ssm_parameter_obj.secretName,
        },
      }
    );

    // Get eventbus object
    const event_bus_obj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    const icav2_bclconvert_success_event_state_machine =
      new BsshIcav2FastqCopyStateMachineConstruct(this, id, {
        /* Metadata */
        prefix: this.bsshIcav2Map.prefix,
        /* Stack objects */
        icav2CopyBatchStateMachineObj: icav2_copy_batch_stack_state_machine_arn_obj,
        icav2JwtSsmParameterObj: icav2_jwt_ssm_parameter_obj,
        eventBusObj: event_bus_obj,
        /* Lambda paths */
        bclconvertSuccessEventHandlerLambdaObj: bclconvert_success_event_lambda,
        /* State machine paths */
        workflowDefinitionBodyPath: path.join(
          __dirname,
          '../step_functions_templates/bclconvert_success_event_state_machine.json'
        ),
      });
  }
}
