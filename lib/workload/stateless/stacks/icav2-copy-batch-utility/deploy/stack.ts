import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { ICAv2CopyBatchUtilityConstruct } from './constructs/icav2-copy-batch-utility';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import path = require('path');

export interface ICAv2CopyBatchUtilityConfig {
  Icav2TokenSecretId: string; //  "ICAv2Jwticav2-credentials-umccr-service-user-trial"
  Icav2CopyBatchStateMachineName: string;
  Icav2CopyBatchStateMachineNameSsmParameterPath: string;
  Icav2CopyBatchStateMachineArnSsmParameterPath: string;
  Icav2CopySingleStateMachineName: string;
  Icav2CopySingleStateMachineNameSsmParameterPath: string;
  Icav2CopySingleStateMachineArnSsmParameterPath: string;
}

export type ICAv2CopyBatchUtilityStackProps = ICAv2CopyBatchUtilityConfig & cdk.StackProps;

export class ICAv2CopyBatchUtilityStack extends cdk.Stack {
  public readonly icav2_copy_batch_state_machine_arn_ssm_parameter_path: string;
  public readonly icav2_copy_batch_state_machine_name_ssm_parameter_path: string;
  public readonly icav2_copy_single_state_machine_arn_ssm_parameter_path: string;
  public readonly icav2_copy_single_state_machine_name_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props: ICAv2CopyBatchUtilityStackProps) {
    super(scope, id, props);

    // Get ICAv2 Access token secret object for construct
    const icav2_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'Icav2SecretsObject',
      props.Icav2TokenSecretId
    );

    // Generate lambda layer
    const lambda_layer = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerDescription: 'ICAv2 Copy Batch Utility Tools',
      layerDirectory: path.join(__dirname, '../layers'),
      layerName: 'icav2_copy_batch_utility_tools',
    });

    // Generate icav2 copy batch stack
    const icav2_copy_batch_state_machine = new ICAv2CopyBatchUtilityConstruct(
      this,
      'icav2_copy_batch_state_machine',
      {
        /* Constructs */
        icav2JwtSecretParameterObj: icav2_access_token_secret_obj,
        lambdasLayer: lambda_layer,
        /* Paths */
        checkOrLaunchJobLambdaPath: path.join(__dirname, '../lambdas/check_or_launch_job'),
        manifestHandlerLambdaPath: path.join(__dirname, '../lambdas/manifest_handler'),
        /* State Machines */
        stateMachineNameBatch: props.Icav2CopyBatchStateMachineName,
        stateMachineNameSingle: props.Icav2CopySingleStateMachineName,
        stateMachineBatchDefinitionBodyPath: path.join(
          __dirname,
          '../step_functions_templates/copy_batch_state_machine.asl.json'
        ),
        stateMachineSingleDefinitionBodyPath: path.join(
          __dirname,
          '../step_functions_templates/copy_single_job_state_machine.asl.json'
        ),
      }
    );

    // Generate ssm parameters for batch and single state machines
    this.icav2_copy_batch_state_machine_arn_ssm_parameter_path =
      props.Icav2CopyBatchStateMachineArnSsmParameterPath;
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_batch_state_machine_arn_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2CopyBatchStateMachine.stateMachineArn,
      'batch_arn'
    );

    this.icav2_copy_single_state_machine_arn_ssm_parameter_path =
      props.Icav2CopySingleStateMachineArnSsmParameterPath;
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_single_state_machine_arn_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2CopySingleStateMachine.stateMachineArn,
      'single_arn'
    );

    this.icav2_copy_batch_state_machine_name_ssm_parameter_path =
      props.Icav2CopyBatchStateMachineNameSsmParameterPath;
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_batch_state_machine_name_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2CopyBatchStateMachine.stateMachineName,
      'batch_name'
    );

    this.icav2_copy_single_state_machine_name_ssm_parameter_path =
      props.Icav2CopySingleStateMachineNameSsmParameterPath;
    this.set_ssm_parameter_obj_for_state_machine(
      this.icav2_copy_single_state_machine_name_ssm_parameter_path,
      icav2_copy_batch_state_machine.icav2CopySingleStateMachine.stateMachineName,
      'single_name'
    );
  }

  private set_ssm_parameter_obj_for_state_machine(
    parameter_name: string,
    state_machine_arn: string,
    parameter_id_midfix: string
  ): ssm.StringParameter {
    /*
    Generate the ssm parameter for the state machine arn
    */
    return new ssm.StringParameter(this, `state_machine_arn_${parameter_id_midfix}_ssm_parameter`, {
      parameterName: parameter_name,
      stringValue: state_machine_arn,
    });
  }
}
