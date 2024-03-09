import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { ctTSOv2LaunchStepFunctionStateMachineConstruct } from '../constructs/cttso_v2_launch_step_function';

interface ctTSOV2LaunchStateMachineStackProps extends cdk.StackProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  icav2_copy_batch_utility_state_machine_ssm_parameter_path: string;
}

export class ctTSOV2LaunchStateMachineStack extends cdk.Stack {

  public readonly cttso_v2_launch_state_machine_arn: string
  public readonly cttso_v2_launch_state_machine_ssm_parameter_path: string

  constructor(scope: Construct, id: string, props: ctTSOV2LaunchStateMachineStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine value from lookup
    // This will allow us to copy the fastq files to the correct location for launch
    const icav2_copy_batch_stack_state_machine_arn_obj = ssm.StringParameter.fromStringParameterName(
        this,
        'icav2_copy_batch_state_machine_ssm_parameter',
        props.icav2_copy_batch_utility_state_machine_ssm_parameter_path
      )

    const cttso_v2_launch_state_machine = new ctTSOv2LaunchStepFunctionStateMachineConstruct(
      this,
      id,
      {
        icav2_jwt_ssm_parameter_path: props.icav2_jwt_ssm_parameter_path,  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
        lambdas_layer_path: __dirname + '/../../../layers/', // __dirname + '/../../../layers
        get_cttso_cache_and_output_paths_lambda_path: __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths', // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
        generate_trimmed_samplesheet_lambda_path: __dirname + '/../../../lambdas/generate_and_trim_cttso_samplesheet_dict', // __dirname + '/../../../lambdas/generate_and_trim_cttso_samplesheet_dict'
        upload_samplesheet_to_cache_dir_lambda_path: __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir', // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
        generate_copy_manifest_dict_lambda_path: __dirname + '/../../../lambdas/generate_copy_manifest_dict', // __dirname + '/../../../lambdas/generate_copy_manifest_dict'
        launch_cttso_nextflow_pipeline_lambda_path: __dirname + '/../../../lambdas/launch_cttso_nextflow_pipeline', // __dirname + '../launch_cttso_nextflow_pipeline'
        ssm_parameter_list: props.ssm_parameter_list, // List of parameters the workflow session state machine will need access to
        icav2_copy_batch_state_machine_arn: icav2_copy_batch_stack_state_machine_arn_obj.stringValue, // The state machine arn for the copy batch utility
        workflow_definition_body_path: __dirname + "/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json", // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'
      }
    );

    // Set outputs
    this.cttso_v2_launch_state_machine_arn = cttso_v2_launch_state_machine.cttso_v2_launch_state_machine_arn
    this.cttso_v2_launch_state_machine_ssm_parameter_path = this.get_ssm_parameter_obj_for_state_machine(
      cttso_v2_launch_state_machine.cttso_v2_launch_state_machine_arn
    ).parameterName

  }

  private get_ssm_parameter_obj_for_state_machine(
    state_machine_arn: string,
  ): ssm.StringParameter {
    /*
    Generate the ssm parameter for the state machine arn
    */
    return new ssm.StringParameter(
      this,
      'state_machine_arn_ssm_parameter',
      {
        parameterName: this.cttso_v2_launch_state_machine_ssm_parameter_path,
        stringValue: state_machine_arn,
      },
    );
  }

}
