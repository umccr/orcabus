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
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pipelineIdSsmPath: string; // List of parameters the workflow session state machine will need access to
  icav2CopyBatchUtilityStateMachineName: string;
  cttsov2LaunchStateMachineArnSsmParameterPath: string;
  cttsov2LaunchStateMachineNameSsmParameterPath: string;
  dynamodbTableName: string;
  eventbusName: string;
  workflowType: string;
  workflowVersion: string;
  serviceVersion: string;
}

export type cttsov2Icav2PipelineManagerStackProps = Cttsov2Icav2PipelineManagerConfig &
  cdk.StackProps;

export class Cttsov2Icav2PipelineManagerStack extends cdk.Stack {
  public readonly cttsov2LaunchStateMachineArn: string;
  public readonly cttsov2LaunchStateMachineName: string;
  public readonly cttsov2LaunchStateMachineArnSsmParameterPath: string;
  public readonly cttsov2LaunchStateMachineNameSsmParameterPath: string;

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

    // Get event bus
    const eventbus_obj = events.EventBus.fromEventBusName(this, 'eventbus', props.eventbusName);

    const cttso_v2_launch_state_machine = new Cttsov2Icav2PipelineManagerConstruct(this, id, {
      /* Stack Objects */
      dynamodbTableObj: dynamodb_table_obj,
      icav2AccessTokenSecretObj: icav2_access_token_secret_obj,
      lambdaLayerObj: lambda_layer_obj.lambdaLayerVersionObj,
      icav2CopyBatchStateMachineObj: icav2_copy_batch_stack_state_machine_obj,
      pipelineIdSSMParameterObj: pipeline_id_ssm_obj_list,
      eventbusObj: eventbus_obj,
      /* Lambdas paths */
      generateDbUuidLambdaPath: path.join(__dirname, '../lambdas/generate_db_uuid'), // __dirname + '/../../../lambdas/generate_uuid'
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
      workflowDefinitionBodyPath: path.join(
        __dirname,
        '../step_functions_templates/cttso_v2_launch_workflow_state_machine.asl.json'
      ), // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.asl.json'
      workflowType: props.workflowType,
      workflowVersion: props.workflowVersion,
      serviceVersion: props.serviceVersion,
    });

    // Set outputs
    this.cttsov2LaunchStateMachineArn = cttso_v2_launch_state_machine.cttsov2LaunchStateMachineArn;
    this.cttsov2LaunchStateMachineName =
      cttso_v2_launch_state_machine.cttsov2LaunchStateMachineName;
    this.cttsov2LaunchStateMachineArnSsmParameterPath =
      props.cttsov2LaunchStateMachineArnSsmParameterPath;
    this.cttsov2LaunchStateMachineNameSsmParameterPath =
      props.cttsov2LaunchStateMachineNameSsmParameterPath;

    // Set SSM Parameter for the state machine arn
    new ssm.StringParameter(this, 'state_machine_arn_ssm_parameter', {
      parameterName: this.cttsov2LaunchStateMachineArnSsmParameterPath,
      stringValue: this.cttsov2LaunchStateMachineArn,
    });

    // Set SSM Parameter for the state machine name
    new ssm.StringParameter(this, 'state_machine_name_ssm_parameter', {
      parameterName: this.cttsov2LaunchStateMachineNameSsmParameterPath,
      stringValue: this.cttsov2LaunchStateMachineName,
    });
  }
}
