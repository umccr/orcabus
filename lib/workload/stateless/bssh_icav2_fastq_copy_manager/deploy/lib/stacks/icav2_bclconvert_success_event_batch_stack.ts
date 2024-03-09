import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { ICAv2WorkflowSessionStateMachineConstruct } from '../constructs/bclconvert_success_event_step_function';

interface ICAv2WorkflowSessionStateMachineStackProps extends cdk.StackProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  icav2_copy_batch_utility_state_machine_ssm_parameter_path: string;  // "/icav2/umccr-prod/copy-batch-state-machine-arn"
  bssh_icav2_fastq_copy_manager_state_machine_ssm_parameter_path: string;  // "/bssh_icav2_fastq_copy/state_machine_arn"
  ssm_parameter_list: string[];

}

export class ICAv2BCLConvertSuccessEventStateMachineStack extends cdk.Stack {

  public readonly icav2_bclconvert_success_event_state_machine_arn: string
  public readonly icav2_bclconvert_success_event_state_machine_ssm_parameter_path: string

  constructor(scope: Construct, id: string, props: ICAv2WorkflowSessionStateMachineStackProps) {
    super(scope, id, props);

    // Get the copy batch state machine value from lookup
    const icav2_copy_batch_stack_state_machine_arn_obj = ssm.StringParameter.fromStringParameterName(
        this,
        'icav2_copy_batch_state_machine_ssm_parameter',
        props.icav2_copy_batch_utility_state_machine_ssm_parameter_path
      )

    const icav2_bclconvert_success_event_state_machine = new ICAv2WorkflowSessionStateMachineConstruct(
      this,
      id,
      {
        icav2_copy_batch_state_machine_arn: icav2_copy_batch_stack_state_machine_arn_obj.stringValue,
        lambdas_layer_path: __dirname + '/../../../layers',
        ssm_parameter_list: props.ssm_parameter_list,
        bclconvert_success_event_handler_path: __dirname + '/../../../lambdas/bclconvert_success_event_handler',
        workflow_definition_body_path: __dirname + '/../../../step_functions_templates/bclconvert_success_event_state_machine.json',
        icav2_jwt_ssm_parameter_path: props.icav2_jwt_ssm_parameter_path,
      }
    )

    // Set outputs
    this.icav2_bclconvert_success_event_state_machine_arn = icav2_bclconvert_success_event_state_machine.icav2_bclconvert_success_event_state_machine_arn
    this.icav2_bclconvert_success_event_state_machine_ssm_parameter_path = this.get_ssm_parameter_obj_for_state_machine(
      icav2_bclconvert_success_event_state_machine.icav2_bclconvert_success_event_state_machine_arn,
      props.bssh_icav2_fastq_copy_manager_state_machine_ssm_parameter_path
    ).parameterName

  }

  private get_ssm_parameter_obj_for_state_machine(
    state_machine_arn: string,
    parameter_name: string
  ): ssm.StringParameter {
    /*
    Generate the ssm parameter for the state machine arn
    */
    return new ssm.StringParameter(
      this,
      'state_machine_arn_ssm_parameter',
      {
        parameterName: parameter_name,
        stringValue: state_machine_arn,
      },
    );
  }

}
