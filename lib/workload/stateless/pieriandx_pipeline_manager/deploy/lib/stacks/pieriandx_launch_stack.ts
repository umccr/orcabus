import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as lambda from 'aws-cdk-lib/aws-lambda'
import { PieriandxLaunchStepFunctionStateMachineConstruct } from '../constructs/pieriandx_launch_step_function';
import { LambdaLayerConstruct } from '../constructs/lambda_layer';
import {
  PieriandxLaunchCaseCreationStepFunctionStateMachineConstruct
} from '../constructs/pieriandx_launch_case_creation_step_function';
import {
  PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstruct
} from '../constructs/pieriandx_launch_informaticsjob_creation_step_function';
import {
  PieriandxLaunchSequencerrunCreationStepFunctionsStateMachineConstruct
} from '../constructs/pieriandx_launch_sequencerrun_creation_step_function'

interface PieriandxLaunchStateMachineStackProps extends cdk.StackProps {
  icav2_token_secret_id: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pieriandx_s3_access_token_secret_id: string; // "/pieriandx/s3AccessCredentials"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  pieriandx_launch_state_machine_arn_ssm_parameter_path: string;
  pieriandx_launch_state_machine_name_ssm_parameter_path: string;
  dynamodb_table_ssm_parameter_path: string;
  pieriandx_user_email: string;
  pieriandx_institution: string;
  pieriandx_base_url: string;
  pieriandx_auth_token_collection_lambda_name: string
}


export class PieriandxLaunchStack extends cdk.Stack {

  public readonly pieriandx_launch_state_machine_arn: string;
  public readonly pieriandx_launch_state_machine_name: string;
  public readonly pieriandx_launch_state_machine_arn_ssm_parameter_path: string;
  public readonly pieriandx_launch_state_machine_name_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props: PieriandxLaunchStateMachineStackProps) {
    super(scope, id, props);

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

    const pieriandx_s3_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this, 'PieriandxS3SecretsObject',
      props.pieriandx_s3_access_token_secret_id,
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

    // Collect the pieriandx access token
    const pieriandx_token_collection_lambda_obj: lambda.IFunction = lambda.Function.fromFunctionName(
      this,
      'pieriandx_auth_token_collection_lambda',
      props.pieriandx_auth_token_collection_lambda_name,
    )

    /* Generate case creation statemachine object */
    const pieriandx_launch_case_creation_state_machine = new PieriandxLaunchCaseCreationStepFunctionStateMachineConstruct(
      this,
      'case_creation',
      {
        /* Stack Objects */
        dynamodb_table_obj: dynamodb_table_obj,
        pieriandx_collect_access_token_lambda_obj: pieriandx_token_collection_lambda_obj,
        lambda_layer_obj: lambda_layer_obj,
        ssm_parameter_obj_list: ssm_parameter_obj_list,
        /* Lambda paths */
        generate_case_lambda_path: __dirname + '/../../../lambdas/generate_case', // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
        /* Step function template */
        launch_pieriandx_case_creation_stepfunction_template: __dirname + '/../../../step_function_templates/launch_pieriandx_case_creation.asl.json', // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'        pieriandx_auth_token_secret_obj: undefined,
        /* Pieriandx Env Configurations */
        pieriandx_user_email: props.pieriandx_user_email,
        pieriandx_institution: props.pieriandx_institution,
        pieriandx_base_url: props.pieriandx_base_url
      }
    )

    /* Generate informatics job creation statemachine object */
    const pieriandx_informaticsjob_creation_state_machine = new PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstruct(
      this,
      'informaticsjob_creation',
      {
        /* Stack Objects */
        dynamodb_table_obj: dynamodb_table_obj,
        pieriandx_collect_access_token_lambda_obj: pieriandx_token_collection_lambda_obj,
        lambda_layer_obj: lambda_layer_obj,
        ssm_parameter_obj_list: ssm_parameter_obj_list,
        /* Lambda paths */
        generate_informatics_job_lambda_path: __dirname + '/../../../lambdas/generate_informaticsjob', // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
        /* Step function templates */
        launch_pieriandx_informaticsjob_creation_stepfunction_template: __dirname + '/../../../step_function_templates/launch_pieriandx_informaticsjob_creation.asl.json', // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'        pieriandx_auth_token_secret_obj: undefined,
        /* Pieriandx Env Configurations */
        pieriandx_user_email: props.pieriandx_user_email,
        pieriandx_institution: props.pieriandx_institution,
        pieriandx_base_url: props.pieriandx_base_url
      }
    )

    /* Generate Sequence Run Creation StateMachine object */
    const pieriandx_sequencerrun_creation_state_machine = new PieriandxLaunchSequencerrunCreationStepFunctionsStateMachineConstruct(
      this,
      'sequencerrun_creation',
      {
        /* Stack Objects */
        dynamodb_table_obj: dynamodb_table_obj,
        pieriandx_collect_access_token_lambda_obj: pieriandx_token_collection_lambda_obj,
        pieriandx_s3_access_token_secret_obj: pieriandx_s3_access_token_secret_obj,
        lambda_layer_obj: lambda_layer_obj,
        ssm_parameter_obj_list: ssm_parameter_obj_list,
        icav2_access_token_secret_obj: icav2_access_token_secret_obj,  // Need to download files from ICAv2
        /* Lambda paths */
        upload_data_to_s3_lambda_path: __dirname + '/../../../lambdas/upload_pieriandx_sample_data_to_s3', // __dirname + '/../../../lambdas/upload_pieriandx_sample_data_to_s3'
        generate_samplesheet_lambda_path: __dirname + '/../../../lambdas/generate_samplesheet', // __dirname + '/../../../lambdas/generate_samplesheet'
        generate_sequencerrun_lambda_path: __dirname + '/../../../lambdas/generate_sequencerrun_case', // __dirname + '/../../../lambdas/generate_sequencerrun_case'
        /* Step function templates */
        launch_pieriandx_sequencerrun_creation_stepfunction_template: __dirname + '/../../../step_function_templates/launch_pieriandx_sequencerrun_creation.asl.json', // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'        pieriandx_auth_token_secret_obj: undefined,
        /* Pieriandx Env Configurations */
        pieriandx_user_email: props.pieriandx_user_email,
        pieriandx_institution: props.pieriandx_institution,
        pieriandx_base_url: props.pieriandx_base_url
      }
    )

    /* Generate parent statemachine object */
    const pieriandx_launch_state_machine = new PieriandxLaunchStepFunctionStateMachineConstruct(
      this,
      id,
      {
        /* Stack Objects */
        dynamodb_table_obj: dynamodb_table_obj,
        lambda_layer_obj: lambda_layer_obj,
        ssm_parameter_obj_list: ssm_parameter_obj_list,
        /* Lambdas paths */
        generate_uuid_lambda_path: __dirname + '/../../../lambdas/generate_uuid', // __dirname + '/../../../lambdas/generate_uuid'
        generate_pieriandx_dx_objects_lambda_path: __dirname + '/../../../lambdas/generate_pieriandx_dx_objects', // __dirname + '/../../../lambdas/generate_and_trim_cttso_samplesheet_dict'
        /* Step function templates */
        launch_pieriandx_stepfunction_template: __dirname + '/../../../step_function_templates/launch_pieriandx.asl.json', // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'
        launch_pieriandx_case_creation_stepfunction_obj: pieriandx_launch_case_creation_state_machine.pieriandx_launch_case_creation_state_machine_obj,
        launch_pieriandx_informaticsjob_creation_stepfunction_obj: pieriandx_informaticsjob_creation_state_machine.pieriandx_launch_informaticsjob_creation_state_machine_obj,
        launch_pieriandx_sequencerrun_creation_stepfunction_obj: pieriandx_sequencerrun_creation_state_machine.pieriandx_launch_sequencerrun_creation_state_machine_obj
      },
    );

    // Set outputs
    this.pieriandx_launch_state_machine_arn = pieriandx_launch_state_machine.pieriandx_launch_state_machine_arn;
    this.pieriandx_launch_state_machine_name = pieriandx_launch_state_machine.pieriandx_launch_state_machine_name;
    this.pieriandx_launch_state_machine_arn_ssm_parameter_path = props.pieriandx_launch_state_machine_arn_ssm_parameter_path;
    this.pieriandx_launch_state_machine_name_ssm_parameter_path = props.pieriandx_launch_state_machine_name_ssm_parameter_path;

    // Set SSM Parameter for the state machine arn
    new ssm.StringParameter(
      this,
      'state_machine_arn_ssm_parameter',
      {
        parameterName: this.pieriandx_launch_state_machine_arn_ssm_parameter_path,
        stringValue: this.pieriandx_launch_state_machine_arn,
      },
    );

    // Set SSM Parameter for the state machine name
    new ssm.StringParameter(
      this,
      'state_machine_name_ssm_parameter',
      {
        parameterName: this.pieriandx_launch_state_machine_name_ssm_parameter_path,
        stringValue: this.pieriandx_launch_state_machine_name,
      },
    );
  }
}
