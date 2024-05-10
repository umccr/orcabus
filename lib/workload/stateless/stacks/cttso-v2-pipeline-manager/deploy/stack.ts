import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import { Cttsov2Icav2PipelineManagerConstruct } from './constructs/cttsov2-icav2-manager';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import path from 'path';

export interface Cttsov2Icav2PipelineManagerConfig {
  /* ICAv2 Pipeline analysis essentials */
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pipelineIdSsmPath: string; // List of parameters the workflow session state machine will need access to
  /* Table to store analyis metadata */
  dynamodbTableName: string;
  /* Internal and external buses */
  eventBusName: string;
  icaEventPipeName: string;
  /*
  Event handling
  */
  workflowType: string;
  workflowVersion: string;
  serviceVersion: string;
  triggerLaunchSource: string;
  internalEventSource: string;
  detailType: string;
  /*
  Names for statemachines
  */
  stateMachinePrefix: string;
  /*
  Extras
  */
  icav2CopyBatchUtilityStateMachineName: string;
}

export type cttsov2Icav2PipelineManagerStackProps = Cttsov2Icav2PipelineManagerConfig &
  cdk.StackProps;

export class Cttsov2Icav2PipelineManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cttsov2Icav2PipelineManagerStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine name
    const icav2_copy_batch_stack_state_machine_obj = sfn.StateMachine.fromStateMachineName(
      this,
      'icav2_copy_batch_state_machine',
      props.icav2CopyBatchUtilityStateMachineName
    );

    // Get dynamodb table for construct
    const dynamodb_table_obj = dynamodb.TableV2.fromTableName(
      this,
      'dynamodb_table',
      props.dynamodbTableName
    );

    // Get ICAv2 Access token secret object for construct
    const icav2_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'Icav2SecretsObject',
      props.icav2TokenSecretId
    );

    // Get lambda layer object
    const lambda_layer_obj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: 'cttso-v2-launch-state-machine-layer',
      layerDescription: 'CTTSO v2 Launch State Machine Lambda Layer',
      layerDirectory: path.join(__dirname, '../layers/'),
    });

    // Set ssm parameter object list
    const pipeline_id_ssm_obj_list = ssm.StringParameter.fromStringParameterName(
      this,
      props.pipelineIdSsmPath,
      props.pipelineIdSsmPath
    );

    // Create the state machine to launch the nextflow workflow on ICAv2
    const cttso_v2_launch_state_machine = new Cttsov2Icav2PipelineManagerConstruct(this, id, {
      /* Stack Objects */
      dynamodbTableObj: dynamodb_table_obj,
      icav2AccessTokenSecretObj: icav2_access_token_secret_obj,
      lambdaLayerObj: lambda_layer_obj.lambdaLayerVersionObj,
      icav2CopyBatchStateMachineObj: icav2_copy_batch_stack_state_machine_obj,
      pipelineIdSsmObj: pipeline_id_ssm_obj_list,
      /* Lambdas paths */
      generateTrimmedSamplesheetLambdaPath: path.join(
        __dirname,
        '../lambdas/generate_and_trim_cttso_samplesheet_dict'
      ), // __dirname + '/../../../lambdas/generate_and_trim_cttso_samplesheet_dict'
      uploadSamplesheetToCacheDirLambdaPath: path.join(
        __dirname,
        '../lambdas/upload_samplesheet_to_cache_dir'
      ), // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
      generateCopyManifestDictLambdaPath: path.join(
        __dirname,
        '../lambdas/generate_copy_manifest_dict'
      ), // __dirname + '/../../../lambdas/generate_copy_manifest_dict'
      launchCttsov2NextflowPipelineLambdaPath: path.join(
        __dirname,
        '../lambdas/launch_cttso_nextflow_pipeline'
      ), // __dirname + '../launch_cttso_nextflow_pipeline'
      /* Step function templates */
      generateInputJsonSfnTemplatePath: path.join(
        __dirname,
        '../step_functions_templates/cttso_v2_launch_workflow_state_machine.asl.json'
      ), // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.asl.json'
      /* Event buses */
      eventBusName: props.eventBusName,
      icaEventPipeName: props.icaEventPipeName,
      /* Event handling */
      detailType: props.detailType,
      serviceVersion: props.serviceVersion,
      triggerLaunchSource: props.triggerLaunchSource,
      internalEventSource: props.internalEventSource,
      stateMachinePrefix: props.stateMachinePrefix,
      workflowType: props.workflowType,
      workflowVersion: props.workflowVersion,
    });
  }
}
