import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BclConvertInteropQcLaunchStepFunctionStateMachineConstruct } from '../constructs/bclconvert_interop_qc_step_function';


interface BclconvertInteropQcPipelineManagerLaunchStateMachineStackProps extends cdk.StackProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  interop_qc_pipeline_dynamodb_ssm_parameter_path: string; // "arn:aws:dynamodb:ap-southeast-2:123456789012:table/interop_qc_pipeline"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  bclconvert_interop_qc_launch_state_machine_ssm_parameter_path: string; // "/icav2/umccr-prod/bclconvert-interop-qc-launch-state-machine-arn"
}

export class BclconvertInteropQcPipelineLaunchStateMachineStack extends cdk.Stack {

  public readonly bclconvert_interop_qc_launch_state_machine_arn: string
  public readonly bclconvert_interop_qc_launch_state_machine_ssm_parameter_path: string

  constructor(scope: Construct, id: string, props: BclconvertInteropQcPipelineManagerLaunchStateMachineStackProps) {
    super(scope, id, props);

    const interop_qc_pipeline_dynamodb_arn = ssm.StringParameter.fromStringParameterName(
      this,
      'interop_qc_pipeline_dynamodb_arn',
      props.interop_qc_pipeline_dynamodb_ssm_parameter_path
    ).stringValue

    
    const bclconvert_interop_qc_launch_state_machine = new BclConvertInteropQcLaunchStepFunctionStateMachineConstruct(
      this,
      id,
      {
        icav2_jwt_ssm_parameter_path: props.icav2_jwt_ssm_parameter_path,  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
        lambdas_layer_path: __dirname + '/../../../layers/', // __dirname + '/../../../layers
        launch_bclconvert_interop_qc_cwl_pipeline_lambda_path: __dirname + '/../../../lambdas/launch_pipeline_analysis', // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
        interop_qc_pipeline_dynamodb_arn: interop_qc_pipeline_dynamodb_arn, // "arn:aws:dynamodb:ap-southeast-2:123456789012:table/interop_qc_pipeline"
        ssm_parameter_list: props.ssm_parameter_list, // List of parameters the workflow session state machine will need access to
        workflow_definition_body_path: __dirname + "/../../../step_functions_templates/launch_bclconvert_interop_qc_pipeline_template.json", // __dirname + '/../../../step_functions_templates/bclconvert_interop_qc_launch_workflow_state_machine.json'
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
