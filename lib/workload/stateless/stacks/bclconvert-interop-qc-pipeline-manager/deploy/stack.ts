import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import { BclConvertInteropQcIcav2PipelineConstruct } from './constructs/bclconvert-interop-qc-step-function';

export interface BclconvertInteropQcIcav2PipelineManagerConfig {
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pipelineIdSsmPath: string; // List of parameters the workflow session state machine will need access to
  dynamodbTableName: string;
  eventBusName: string;
  icaEventPipeName: string;
  /*
  Event handling
  */
  workflowType: string;
  workflowVersion: string;
  serviceVersion: string;
  triggerLaunchSource: string;
  internalEventSource: string;
  detailType: string;
  /*
  Names for statemachines
  */
  stateMachinePrefix: string;
}

export type BclconvertInteropQcIcav2PipelineManagerStackProps =
  BclconvertInteropQcIcav2PipelineManagerConfig & cdk.StackProps;

export class BclconvertInteropQcIcav2PipelineManagerStack extends cdk.Stack {
  public readonly bclconvertInteropQcLaunchStateMachineObj: string;

  constructor(
    scope: Construct,
    id: string,
    props: BclconvertInteropQcIcav2PipelineManagerStackProps
  ) {
    super(scope, id, props);

    // Get dynamodb table for construct
    const dynamodb_table_obj = dynamodb.TableV2.fromTableName(
      this,
      'bclconvertInteropQcICAv2AnalysesDynamoDBTable',
      props.dynamodbTableName
    );

    // Get ICAv2 Access token secret object for construct
    const icav2_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'Icav2SecretsObject',
      props.icav2TokenSecretId
    );

    // Get pipelineId
    const pipeline_id_ssm_obj = ssm.StringParameter.fromStringParameterName(
      this,
      'PipelineIdSsmParameter',
      props.pipelineIdSsmPath
    );

    // Create the state machines and lambdas.
    // Connect permissions for statemachines to access the dynamodb table and launch lambda functions
    // Connect permissions for lambdas to access the secrets manager
    const bclconvert_interop_qc_launch_state_machine =
      new BclConvertInteropQcIcav2PipelineConstruct(this, id, {
        // Stack objects
        dynamodbTableObj: dynamodb_table_obj,
        icav2AccessTokenSecretObj: icav2_access_token_secret_obj,
        pipelineIdSsmObj: pipeline_id_ssm_obj,
        // Step function template paths
        generateInputJsonSfnTemplatePath: path.join(
          __dirname,
          '../step_functions_templates/set_bclconvert_interop_qc_cwl_inputs_and_launch_pipeline_sfn.json'
        ),
        // Event buses
        eventBusName: props.eventBusName,
        icaEventPipeName: props.icaEventPipeName,
        // Event handling
        detailType: props.detailType,
        serviceVersion: props.serviceVersion,
        triggerLaunchSource: props.triggerLaunchSource,
        internalEventSource: props.internalEventSource,
        stateMachinePrefix: props.stateMachinePrefix,
        workflowType: props.workflowType,
        workflowVersion: props.workflowVersion,
      });

    // Set outputs
    this.bclconvertInteropQcLaunchStateMachineObj =
      bclconvert_interop_qc_launch_state_machine.handleWfmReadyEventStateMachineObj;
  }
}
