import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BclConvertInteropQcLaunchStepFunctionStateMachineConstruct } from '../constructs/bclconvert_interop_qc_step_function';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { LambdaLayerConstruct } from '../constructs/lambda_layer';

interface BclconvertInteropQcPipelineManagerLaunchStateMachineStackProps extends cdk.StackProps {
  dynamodb_name_ssm_parameter_path: string;  // "/umccr/orcabus/stateful/bclconvert_interop_qc_pipeline_dynamo_db/analysis_table_name"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  bclconvert_interop_qc_launch_state_machine_ssm_parameter_path: string; // "/icav2/umccr-prod/bclconvert-interop-qc-launch-state-machine-arn"
  icav2_token_secret_id: string; // "ICAv2Jwticav2-credentials-umccr-service-user-trial"
}

export class BclconvertInteropQcPipelineLaunchStateMachineStack extends cdk.Stack {

  public readonly bclconvert_interop_qc_launch_state_machine_arn: string
  public readonly bclconvert_interop_qc_launch_state_machine_ssm_parameter_path: string

  constructor(scope: Construct, id: string, props: BclconvertInteropQcPipelineManagerLaunchStateMachineStackProps) {
    super(scope, id, props);

    // Get dynamodb table for construct
    const dynamic_table_name_str = ssm.StringParameter.fromStringParameterName(
      this,
      'dynamic_table_name',
      props.dynamodb_name_ssm_parameter_path
    ).stringValue
    const dynamodb_table_obj = dynamodb.TableV2.fromTableName(
      this,
      'bclconvertInteropQcICAv2AnalysesDynamoDBTable',
      dynamic_table_name_str
    )

    // Get ICAv2 Access token secret object for construct
    const icav2_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this, 'Icav2SecretsObject',
      props.icav2_token_secret_id,
    );

    // Set lambda layer object for construct
    const lambda_layer_obj = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: __dirname + '/../../../layers/', // __dirname + '/../../../layers
      });

    // Set ssm parameter object list
    const ssm_parameter_obj_list = props.ssm_parameter_list.map(
      (ssm_parameter_path: string) => ssm.StringParameter.fromStringParameterName(
        this,
        ssm_parameter_path,
        ssm_parameter_path
      )
    )

    // Create the state machines and lambdas.
    // Connect permissions for statemachines to access the dynamodb table and launch lambda functions
    // Connect permissions for lambdas to access the secrets manager
    const bclconvert_interop_qc_launch_state_machine = new BclConvertInteropQcLaunchStepFunctionStateMachineConstruct(
      this,
      id,
      {
        // Stack objects
        dynamodb_table_obj: dynamodb_table_obj,
        icav2_access_token_secret_obj: icav2_access_token_secret_obj,
        lambda_layer_obj: lambda_layer_obj,
        // Lambdas / layers paths
        generate_uuid_lambda_path: __dirname + '/../../../lambdas/generate_db_uuid',
        launch_bclconvert_interop_qc_cwl_pipeline_lambda_path: __dirname + '/../../../lambdas/launch_pipeline_analysis', // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
        // Step function template paths
        state_change_definition_body_path: __dirname + '/../../../step_functions_templates/handle_state_change_template.json',
        launch_workflow_definition_body_path: __dirname + "/../../../step_functions_templates/launch_bclconvert_interop_qc_pipeline_template.json", // __dirname + '/../../../step_functions_templates/bclconvert_interop_qc_launch_workflow_state_machine.json'
        ssm_parameter_obj_list: ssm_parameter_obj_list // List of parameters the workflow session state machine will need access to
      }
    );

    // Set outputs
    this.bclconvert_interop_qc_launch_state_machine_arn = bclconvert_interop_qc_launch_state_machine.bclconvert_interop_qc_pipeline_launch_statemachine_arn
    this.bclconvert_interop_qc_launch_state_machine_ssm_parameter_path = props.bclconvert_interop_qc_launch_state_machine_ssm_parameter_path

    this.set_ssm_parameter_obj_for_state_machine(
      bclconvert_interop_qc_launch_state_machine.bclconvert_interop_qc_pipeline_launch_statemachine_arn
    )
  }

  private set_ssm_parameter_obj_for_state_machine(
    state_machine_arn: string,
  ): ssm.StringParameter {
    /*
    Generate the ssm parameter for the state machine arn
    */
    return new ssm.StringParameter(
      this,
      'state_machine_arn_ssm_parameter',
      {
        parameterName: this.bclconvert_interop_qc_launch_state_machine_ssm_parameter_path,
        stringValue: state_machine_arn,
      },
    );
  }

}
