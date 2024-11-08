/*
Standard ICAv2 compression manager

Uses the ICAv2 framework with a custom sfn inputs and outputs.

Then also listens to the workflowManager success events with an 'add-on' step function that performs the following:

1. Reads in the fastq_gzipped.filesizes.tsv file.
2. Reads in the fastq_gzipped.md5.txt file.
3. Reads in the fastq_ora.md5.txt file
4. Reads in the fastq_ora.filesizes.tsv file.
5. Reads in the fastq_list_ora.csv file.

Generates an event for each fastq file pair with the following
1. The md5sum for both the compressed and uncompressed files
2. The file sizes for both the gzipped compressed and ora compressed files
3. The ratio of the gzipped compressed file size to the ora compressed file size

From here we can start to determine if the compression ratio is worth the FPGA costs or not.

*/

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { Duration } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct } from '../../../../components/sfn-icav2-ready-event-handler';
import { Icav2AnalysisEventHandlerConstruct } from '../../../../components/sfn-icav2-state-change-event-handler';

export interface OraCompressionIcav2PipelineManagerConfig {
  /*
  Tables
  */
  dynamodbTableName: string;

  /*
  Event handling
  */
  eventBusName: string;
  icaEventPipeName: string;
  workflowName: string;
  workflowVersion: string;
  serviceVersion: string;
  triggerLaunchSource: string;
  internalEventSource: string;
  detailType: string;

  /*
  Names for statemachines
  */
  stateMachinePrefix: string;

  /*
  SSM Parameters
  */
  referenceUriSsmPath: string;
  pipelineIdSsmPath: string; // List of parameters the workflow session state machine will need access to

  /*
  Secrets
  */
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
}

export type OraCompressionIcav2PipelineManagerStackProps =
  OraCompressionIcav2PipelineManagerConfig & cdk.StackProps;

export class OraCompressionIcav2PipelineManagerStack extends cdk.Stack {
  public readonly OraCompressionLaunchStateMachineObj: string;
  private globals = {
    workflowManagerSource: 'orcabus.workflowmanager',
    outputCompressionDetailType: 'FastqListRowCompressed',
    analysisStorageSize: 'LARGE', // 7.2 Tb
  };

  constructor(scope: Construct, id: string, props: OraCompressionIcav2PipelineManagerStackProps) {
    super(scope, id, props);

    // Get dynamodb table for construct
    const dynamodbTableObj = dynamodb.TableV2.fromTableName(
      this,
      'bclconvertInteropQcICAv2AnalysesDynamoDBTable',
      props.dynamodbTableName
    );

    // Get ICAv2 Access token secret object for construct
    const icav2AccessTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'Icav2SecretsObject',
      props.icav2TokenSecretId
    );

    // Get pipelineId
    const pipelineIdSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      'PipelineIdSsmParameter',
      props.pipelineIdSsmPath
    );
    const referenceUriSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      'ReferenceUriSsmParameter',
      props.referenceUriSsmPath
    );

    // Get the event bus object
    const eventBusObj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    /*
    Generate the inputs sfn
    */
    const configureInputsSfn = new sfn.StateMachine(this, 'configure_inputs_sfn', {
      stateMachineName: `${props.stateMachinePrefix}-configure-inputs-json`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/set_compression_inputs.asl.json')
      ),
      definitionSubstitutions: {
        __table_name__: dynamodbTableObj.tableName,
        __reference_uri_ssm_parameter_path__: referenceUriSsmObj.parameterName,
      },
    });

    // Configure inputs step function needs to read-write to the dynamodb table
    dynamodbTableObj.grantReadWriteData(configureInputsSfn);

    // Configure step function allow read access to the ssm parameter path
    referenceUriSsmObj.grantRead(configureInputsSfn);

    /*
    Generate the outputs sfn
    */

    // Generate the lambda function to build the outputs json
    const setOutputsJsonLambdaFunctionObj = new PythonFunction(
      this,
      'set_outputs_json_lambda_function',
      {
        runtime: Runtime.PYTHON_3_12,
        entry: path.join(__dirname, '../lambdas/set_outputs_json_py'),
        architecture: Architecture.ARM_64,
        handler: 'handler',
        index: 'set_outputs_json.py',
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
        timeout: Duration.seconds(60),
      }
    );

    // Give the lambda function access to the secret
    icav2AccessTokenSecretObj.grantRead(setOutputsJsonLambdaFunctionObj.currentVersion);

    // Generate outputs
    const configureOutputsSfn = new sfn.StateMachine(this, 'configure_outputs_sfn', {
      stateMachineName: `${props.stateMachinePrefix}-configure-outputs-json`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/set_compression_outputs.asl.json')
      ),
      definitionSubstitutions: {
        __table_name__: dynamodbTableObj.tableName,
        __set_outputs_json_lambda_function_arn__:
          setOutputsJsonLambdaFunctionObj.currentVersion.functionArn,
      },
    });

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(configureOutputsSfn);

    // Configure step function invoke access to the lambda function
    setOutputsJsonLambdaFunctionObj.currentVersion.grantInvoke(configureOutputsSfn);

    // Generate state machine for handling the 'READY' event
    const handleWfmReadyEventSfn = new WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct(
      this,
      'handle_wfm_ready_event',
      {
        tableName: dynamodbTableObj.tableName,
        stateMachineName: `${props.stateMachinePrefix}-wfm-ready-event-handler`,
        icav2AccessTokenSecretObj: icav2AccessTokenSecretObj,
        workflowPlatformType: 'cwl', // Hardcoded this pipeline is a CWL pipeline.
        detailType: props.detailType,
        eventBusName: props.eventBusName,
        triggerLaunchSource: props.triggerLaunchSource,
        internalEventSource: props.internalEventSource,
        generateInputsJsonSfn: configureInputsSfn,
        pipelineIdSsmPath: pipelineIdSsmObj.parameterName,
        workflowName: props.workflowName,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
        analysisStorageSize: this.globals.analysisStorageSize,
      }
    ).stateMachineObj;

    // Generate state machine for handling the external ICAv2 event
    const handleExternalIcav2EventSfn = new Icav2AnalysisEventHandlerConstruct(
      this,
      'handle_interop_qc_ready_event',
      {
        tableName: dynamodbTableObj.tableName,
        stateMachineName: `${props.stateMachinePrefix}-icav2-external-handler`,
        detailType: props.detailType,
        eventBusName: props.eventBusName,
        icaEventPipeName: props.icaEventPipeName,
        internalEventSource: props.internalEventSource,
        generateOutputsJsonSfn: configureOutputsSfn,
        workflowName: props.workflowName,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      }
    ).stateMachineObj;

    // Generate the state machine for generating the fastq list row compression events
    // First need the lambda
    const setMergeSizesLambdaObj = new PythonFunction(this, 'set_merge_sizes_lambda_obj', {
      runtime: Runtime.PYTHON_3_12,
      entry: path.join(__dirname, '../lambdas/merge_file_sizes_for_fastq_list_rows_py'),
      architecture: Architecture.ARM_64,
      handler: 'handler',
      index: 'merge_file_sizes_for_fastq_list_rows.py',
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
      },
      timeout: Duration.seconds(120),
      memorySize: 1024,
    });
    // Give the lambda function access to the secret
    icav2AccessTokenSecretObj.grantRead(setMergeSizesLambdaObj.currentVersion);

    /*
    Part 3 - add on service to collect outputs from the succeeded v2 workflow and generate the fastq list row compression events
    */
    const generateFastqListRowCompressionEventsSfn = new sfn.StateMachine(
      this,
      'generate_fastq_list_row_compression_events_sfn',
      {
        stateMachineName: `${props.stateMachinePrefix}-generate-fqlr-ora-events`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            '../step_functions_templates/fastq_list_row_compression_event.asl.json'
          )
        ),
        definitionSubstitutions: {
          __event_bus_name__: eventBusObj.eventBusName,
          __detail_type__: this.globals.outputCompressionDetailType,
          __merge_sizes_lambda_function_arn__: setMergeSizesLambdaObj.currentVersion.functionArn,
        },
      }
    );

    // Configure step function invoke access to the lambda function
    setMergeSizesLambdaObj.currentVersion.grantInvoke(generateFastqListRowCompressionEventsSfn);

    // Allow the step functions to submit events to the event bus
    eventBusObj.grantPutEventsTo(generateFastqListRowCompressionEventsSfn);

    // Generate rule to trigger the fastq list row compression events
    const generateFastqListRowCompressionEventsRule = new events.Rule(
      this,
      'generate_fastq_list_row_compression_events_rule',
      {
        eventBus: eventBusObj,
        ruleName: `${props.stateMachinePrefix}-generate-fqlr-ora-events-rule`,
        eventPattern: {
          source: [this.globals.workflowManagerSource],
          detailType: [props.detailType],
          detail: {
            workflowName: [{ 'equals-ignore-case': props.workflowName }],
            status: [{ 'equals-ignore-case': 'SUCCEEDED' }],
          },
        },
      }
    );

    // Add the target to the rule
    generateFastqListRowCompressionEventsRule.addTarget(
      new eventsTargets.SfnStateMachine(generateFastqListRowCompressionEventsSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
