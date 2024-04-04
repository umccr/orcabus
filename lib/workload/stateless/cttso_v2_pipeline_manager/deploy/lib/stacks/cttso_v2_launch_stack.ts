import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { ctTSOv2LaunchStepFunctionStateMachineConstruct } from '../constructs/cttso_v2_launch_step_function';
import { LambdaLayerConstruct } from '../constructs/lambda_layer';

interface ctTSOV2LaunchStateMachineStackProps extends cdk.StackProps {
  icav2_token_secret_id: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  icav2_copy_batch_utility_state_machine_name_ssm_parameter_path: string;
  cttso_v2_launch_state_machine_arn_ssm_parameter_path: string;
  cttso_v2_launch_state_machine_name_ssm_parameter_path: string;
  dynamodb_table_ssm_parameter_path: string;
}

export class ctTSOV2LaunchStateMachineStack extends cdk.Stack {

  public readonly cttso_v2_launch_state_machine_arn: string;
  public readonly cttso_v2_launch_state_machine_name: string;
  public readonly cttso_v2_launch_state_machine_arn_ssm_parameter_path: string;
  public readonly cttso_v2_launch_state_machine_name_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props: ctTSOV2LaunchStateMachineStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine value from lookup
    // This will allow us to copy the fastq files to the correct location for launch
    const icav2_copy_batch_stack_state_machine_name_obj = ssm.StringParameter.fromStringParameterName(
      this,
      'icav2_copy_batch_state_machine_ssm_parameter',
      props.icav2_copy_batch_utility_state_machine_name_ssm_parameter_path,
    );
    const icav2_copy_batch_stack_state_machine_obj = sfn.StateMachine.fromStateMachineName(
      this,
      'icav2_copy_batch_state_machine',
      icav2_copy_batch_stack_state_machine_name_obj.stringValue,
    );

    // Get the dynamodb table ssm parameter
    const dynamodb_table_ssm_parameter_obj = ssm.StringParameter.fromStringParameterName(
      this,
      'dynamodb_table_ssm_parameter',
      props.dynamodb_table_ssm_parameter_path,
    );
    // Get dynamodb table for construct
    const dynamodb_table_obj = dynamodb.TableV2.fromTableName(
      this,
      'dynamodb_table',
      dynamodb_table_ssm_parameter_obj.stringValue,
    );

    // Get ICAv2 Access token secret object for construct
    const icav2_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this, 'Icav2SecretsObject',
      props.icav2_token_secret_id,
    );

    // Get lambda layer object
    const lambda_layer_obj = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: __dirname + '/../../../layers/', // __dirname + '/../../../layers
      });

    // Set ssm parameter object list
    const ssm_parameter_obj_list = props.ssm_parameter_list.map(
      (ssm_parameter_path: string) => ssm.StringParameter.fromStringParameterName(
        this,
        ssm_parameter_path,
        ssm_parameter_path,
      ),
    );

    const cttso_v2_launch_state_machine = new ctTSOv2LaunchStepFunctionStateMachineConstruct(
      this,
      id,
      {
        /* Stack Objects */
        dynamodb_table_obj: dynamodb_table_obj,
        icav2_access_token_secret_obj: icav2_access_token_secret_obj,
        lambda_layer_obj: lambda_layer_obj,
        icav2_copy_batch_state_machine_obj: icav2_copy_batch_stack_state_machine_obj,
        ssm_parameter_obj_list: ssm_parameter_obj_list,
        /* Lambdas paths */
        generate_db_uuid_lambda_path: __dirname + '/../../../lambdas/generate_db_uuid', // __dirname + '/../../../lambdas/generate_uuid'
        generate_trimmed_samplesheet_lambda_path: __dirname + '/../../../lambdas/generate_and_trim_cttso_samplesheet_dict', // __dirname + '/../../../lambdas/generate_and_trim_cttso_samplesheet_dict'
        upload_samplesheet_to_cache_dir_lambda_path: __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir', // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
        generate_copy_manifest_dict_lambda_path: __dirname + '/../../../lambdas/generate_copy_manifest_dict', // __dirname + '/../../../lambdas/generate_copy_manifest_dict'
        launch_cttso_nextflow_pipeline_lambda_path: __dirname + '/../../../lambdas/launch_cttso_nextflow_pipeline', // __dirname + '../launch_cttso_nextflow_pipeline'
        /* Step function templates */
        workflow_definition_body_path: __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json', // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'
      },
    );

    // Set outputs
    this.cttso_v2_launch_state_machine_arn = cttso_v2_launch_state_machine.cttso_v2_launch_state_machine_arn;
    this.cttso_v2_launch_state_machine_name = cttso_v2_launch_state_machine.cttso_v2_launch_state_machine_name;
    this.cttso_v2_launch_state_machine_arn_ssm_parameter_path = props.cttso_v2_launch_state_machine_arn_ssm_parameter_path;
    this.cttso_v2_launch_state_machine_name_ssm_parameter_path = props.cttso_v2_launch_state_machine_name_ssm_parameter_path;

    // Set SSM Parameter for the state machine arn
    new ssm.StringParameter(
      this,
      'state_machine_arn_ssm_parameter',
      {
        parameterName: this.cttso_v2_launch_state_machine_arn_ssm_parameter_path,
        stringValue: this.cttso_v2_launch_state_machine_arn,
      },
    );

    // Set SSM Parameter for the state machine name
    new ssm.StringParameter(
      this,
      'state_machine_name_ssm_parameter',
      {
        parameterName: this.cttso_v2_launch_state_machine_name_ssm_parameter_path,
        stringValue: this.cttso_v2_launch_state_machine_name,
      },
    );

  }

}
