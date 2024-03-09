import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { ICAv2CopyBatchUtilityConstruct } from '../constructs/icav2_copy_batch_utility';

// import * as sqs from 'aws-cdk-lib/aws-sqs';
interface ICAv2CopyBatchUtilityStackStackProps extends cdk.StackProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  icav2_copy_batch_state_machine_ssm_parameter_path: string;
}

export class ICAv2CopyBatchUtilityStack extends cdk.Stack {

  public readonly icav2_copy_batch_state_machine_arn: string
  public readonly icav2_copy_batch_state_machine_ssm_parameter_path: string

  constructor(scope: Construct, id: string, props: ICAv2CopyBatchUtilityStackStackProps) {
    super(scope, id, props);

    // Generate icav2 copy batch stack
    const icav2_copy_batch_state_machine = new ICAv2CopyBatchUtilityConstruct(
      this,
      'icav2_copy_batch_state_machine',
      {
        copy_batch_data_lambda_path: __dirname + '/../../../lambdas/copy_batch_data_handler',
        definition_body_path: __dirname + '/../../../step_functions_templates/copy_batch_state_machine.json',
        icav2_jwt_ssm_parameter_path: props.icav2_jwt_ssm_parameter_path,
        job_status_handler_lambda_path: __dirname + '/../../../lambdas/job_status_handler',
        lambdas_layer_path: __dirname + '/../../../layers',
        manifest_handler_lambda_path: __dirname + '/../../../lambdas/manifest_handler'
      }
    )

    // Set Attributes
    this.icav2_copy_batch_state_machine_arn = icav2_copy_batch_state_machine.icav2_copy_batch_state_machine_arn
    this.icav2_copy_batch_state_machine_ssm_parameter_path = props.icav2_copy_batch_state_machine_ssm_parameter_path

    // Generate ssm parameter
    this.set_ssm_parameter_obj_for_state_machine(
      icav2_copy_batch_state_machine.icav2_copy_batch_state_machine_arn
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
        parameterName: this.icav2_copy_batch_state_machine_ssm_parameter_path,
        stringValue: state_machine_arn,
      },
    );
  }

}
