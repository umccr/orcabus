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
  icav2_token_secret_id: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  icav2_copy_batch_utility_state_machine_name: string;
  cttso_v2_launch_state_machine_arn_ssm_parameter_path: string;
  cttso_v2_launch_state_machine_name_ssm_parameter_path: string;
  dynamodb_table_name: string;
  eventbus_name: string;
}

export type cttsov2Icav2PipelineManagerStackProps = Cttsov2Icav2PipelineManagerConfig &
  cdk.StackProps;

export class Cttsov2Icav2PipelineManagerStack extends cdk.Stack {
  public readonly cttso_v2_launch_state_machine_arn: string;
  public readonly cttso_v2_launch_state_machine_name: string;
  public readonly cttso_v2_launch_state_machine_arn_ssm_parameter_path: string;
  public readonly cttso_v2_launch_state_machine_name_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props: cttsov2Icav2PipelineManagerStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine name
    const icav2_copy_batch_stack_state_machine_obj = sfn.StateMachine.fromStateMachineName(
      this,
      'icav2_copy_batch_state_machine',
      props.icav2_copy_batch_utility_state_machine_name
    );

    // Get dynamodb table for construct
    const dynamodb_table_obj = dynamodb.TableV2.fromTableName(
      this,
      'dynamodb_table',
      props.dynamodb_table_name
    );

    // Get ICAv2 Access token secret object for construct
    const icav2_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'Icav2SecretsObject',
      props.icav2_token_secret_id
    );

    // Get lambda layer object
    const lambda_layer_obj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layer_name: 'cttso-v2-launch-state-machine-layer',
      layer_description: 'CTTSO v2 Launch State Machine Lambda Layer',
      layer_directory: path.join(__dirname, '../layers/'),
    });

    // Set ssm parameter object list
    const ssm_parameter_obj_list = props.ssm_parameter_list.map((ssm_parameter_path: string) =>
      ssm.StringParameter.fromStringParameterName(this, ssm_parameter_path, ssm_parameter_path)
    );

    // Get event bus
    const eventbus_obj = events.EventBus.fromEventBusName(this, 'eventbus', props.eventbus_name);

    const cttso_v2_launch_state_machine = new Cttsov2Icav2PipelineManagerConstruct(this, id, {
      /* Stack Objects */
      dynamodb_table_obj: dynamodb_table_obj,
      icav2_access_token_secret_obj: icav2_access_token_secret_obj,
      lambda_layer_obj: lambda_layer_obj.lambda_layer_version_obj,
      icav2_copy_batch_state_machine_obj: icav2_copy_batch_stack_state_machine_obj,
      ssm_parameter_obj_list: ssm_parameter_obj_list,
      eventbus_obj: eventbus_obj,
      /* Lambdas paths */
      generate_db_uuid_lambda_path: path.join(__dirname, '../lambdas/generate_db_uuid'), // __dirname + '/../../../lambdas/generate_uuid'
      generate_trimmed_samplesheet_lambda_path: path.join(
        __dirname,
        '../lambdas/generate_and_trim_cttso_samplesheet_dict'
      ), // __dirname + '/../../../lambdas/generate_and_trim_cttso_samplesheet_dict'
      upload_samplesheet_to_cache_dir_lambda_path: path.join(
        __dirname,
        '../lambdas/upload_samplesheet_to_cache_dir'
      ), // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
      generate_copy_manifest_dict_lambda_path: path.join(
        __dirname,
        '../lambdas/generate_copy_manifest_dict'
      ), // __dirname + '/../../../lambdas/generate_copy_manifest_dict'
      launch_cttso_nextflow_pipeline_lambda_path: path.join(
        __dirname,
        '../lambdas/launch_cttso_nextflow_pipeline'
      ), // __dirname + '../launch_cttso_nextflow_pipeline'
      /* Step function templates */
      workflow_definition_body_path: path.join(
        __dirname,
        '../step_functions_templates/cttso_v2_launch_workflow_state_machine.asl.json'
      ), // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.asl.json'
    });

    // Set outputs
    this.cttso_v2_launch_state_machine_arn =
      cttso_v2_launch_state_machine.cttso_v2_launch_state_machine_arn;
    this.cttso_v2_launch_state_machine_name =
      cttso_v2_launch_state_machine.cttso_v2_launch_state_machine_name;
    this.cttso_v2_launch_state_machine_arn_ssm_parameter_path =
      props.cttso_v2_launch_state_machine_arn_ssm_parameter_path;
    this.cttso_v2_launch_state_machine_name_ssm_parameter_path =
      props.cttso_v2_launch_state_machine_name_ssm_parameter_path;

    // Set SSM Parameter for the state machine arn
    new ssm.StringParameter(this, 'state_machine_arn_ssm_parameter', {
      parameterName: this.cttso_v2_launch_state_machine_arn_ssm_parameter_path,
      stringValue: this.cttso_v2_launch_state_machine_arn,
    });

    // Set SSM Parameter for the state machine name
    new ssm.StringParameter(this, 'state_machine_name_ssm_parameter', {
      parameterName: this.cttso_v2_launch_state_machine_name_ssm_parameter_path,
      stringValue: this.cttso_v2_launch_state_machine_name,
    });
  }
}
