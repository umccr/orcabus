import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { ICAv2CopyBatchUtilityConstruct } from '../constructs/icav2_copy_batch_utility';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { LambdaLayerConstruct } from '../constructs/lambda_layer';

// import * as sqs from 'aws-cdk-lib/aws-sqs';
interface ICAv2CopyBatchUtilityStackStackProps extends cdk.StackProps {
  icav2_token_secret_id: string;  //  "ICAv2Jwticav2-credentials-umccr-service-user-trial"
  icav2_copy_batch_state_machine_name_ssm_parameter_path: string;
  icav2_copy_batch_state_machine_arn_ssm_parameter_path: string;
  icav2_copy_single_state_machine_name_ssm_parameter_path: string;
  icav2_copy_single_state_machine_arn_ssm_parameter_path: string;
}

export class ICAv2CopyBatchUtilityStack extends cdk.Stack {

  public readonly icav2_copy_batch_state_machine_arn_ssm_parameter_path: string
  public readonly icav2_copy_batch_state_machine_name_ssm_parameter_path: string
  public readonly icav2_copy_single_state_machine_arn_ssm_parameter_path: string
  public readonly icav2_copy_single_state_machine_name_ssm_parameter_path: string

  constructor(scope: Construct, id: string, props: ICAv2CopyBatchUtilityStackStackProps) {
    super(scope, id, props);

    // Get ICAv2 Access token secret object for construct
    const icav2_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this, 'Icav2SecretsObject',
      props.icav2_token_secret_id,
    );

      // Generate lambda layer
    const lambda_layer = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: __dirname + '/../../../layers',
        layer_name: 'icav2_copy_batch_utility_tools'
      });


    // Generate icav2 copy batch stack
    const icav2_copy_batch_state_machine = new ICAv2CopyBatchUtilityConstruct(
      this,
      'icav2_copy_batch_state_machine',
      {
        /* Constructs */
        icav2_jwt_secret_parameter_obj: icav2_access_token_secret_obj,
        lambdas_layer: lambda_layer,
        /* Paths */
        check_or_launch_job_lambda_path: __dirname + '/../../../lambdas/check_or_launch_job',
        manifest_handler_lambda_path: __dirname + '/../../../lambdas/manifest_handler',
        /* State Machines */
        state_machine_batch_definition_body_path: __dirname + '/../../../step_functions_templates/copy_batch_state_machine.json',
        state_machine_single_definition_body_path: __dirname + '/../../../step_functions_templates/copy_single_job_state_machine.json',
      }
    )

    // Generate ssm parameters for batch and single state machines

    this.icav2_copy_batch_state_machine_arn_ssm_parameter_path = props.icav2_copy_batch_state_machine_arn_ssm_parameter_path
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_batch_state_machine_arn_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2_copy_batch_state_machine.stateMachineArn,
      "batch_arn"
    )

    this.icav2_copy_single_state_machine_arn_ssm_parameter_path = props.icav2_copy_single_state_machine_arn_ssm_parameter_path
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_single_state_machine_arn_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2_copy_single_state_machine.stateMachineArn,
      "single_arn"
    )

    this.icav2_copy_batch_state_machine_name_ssm_parameter_path = props.icav2_copy_batch_state_machine_name_ssm_parameter_path
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_batch_state_machine_name_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2_copy_batch_state_machine.stateMachineName,
      "batch_name"
    )

    this.icav2_copy_single_state_machine_name_ssm_parameter_path = props.icav2_copy_single_state_machine_name_ssm_parameter_path
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_single_state_machine_name_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2_copy_single_state_machine.stateMachineName,
      "single_name"
    )
  }

  private set_ssm_parameter_obj_for_state_machine(
    parameter_name: string,
    state_machine_arn: string,
    parameter_id_midfix: string
  ): ssm.StringParameter {
    /*
    Generate the ssm parameter for the state machine arn
    */
    return new ssm.StringParameter(
      this,
      `state_machine_arn_${parameter_id_midfix}_ssm_parameter`,
      {
        parameterName: parameter_name,
        stringValue: state_machine_arn,
      },
    );
  }

}
