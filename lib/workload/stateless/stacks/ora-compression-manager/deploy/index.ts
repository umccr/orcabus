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
import { OraDecompressionConstruct } from '../../../../components/ora-file-decompression-fq-pair-sfn';
import * as iam from 'aws-cdk-lib/aws-iam';
import { GzipRawMd5sumDecompressionConstruct } from '../../../../components/gzip-raw-md5sum-fq-pair-sfn';
import { NagSuppressions } from 'cdk-nag';

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
  private globals = {
    workflowManagerSource: 'orcabus.workflowmanager',
    outputCompressionDetailType: 'FastqListRowCompressed',
    analysisStorageSize: 'LARGE', // 7.2 Tb
    tablePartitionNames: {
      fastqListRow: 'fastq_list_row',
      instrumentRunId: 'instrument_run_id',
      portalRunId: 'portal_run_id',
    },
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
    Generate input lambdas
    */
    const getV2SamplesheetUriLambdaObj = new PythonFunction(
      this,
      'get_v2_samplesheet_uri_lambda_function_arn',
      {
        runtime: Runtime.PYTHON_3_12,
        entry: path.join(__dirname, '../lambdas/find_all_v2_samplesheets_in_instrument_run_py'),
        architecture: Architecture.ARM_64,
        handler: 'handler',
        index: 'find_all_v2_samplesheets_in_instrument_run.py',
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
        memorySize: 1024,
        timeout: Duration.seconds(300),
      }
    );
    const findAllFastqPairsInInstrumentRunLambdaObj = new PythonFunction(
      this,
      'find_all_fastq_pairs_in_instrument_run_py',
      {
        runtime: Runtime.PYTHON_3_12,
        entry: path.join(__dirname, '../lambdas/find_all_fastq_pairs_in_instrument_run_py'),
        architecture: Architecture.ARM_64,
        handler: 'handler',
        index: 'find_all_fastq_pairs_in_instrument_run.py',
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
        memorySize: 1024,
        timeout: Duration.seconds(300),
      }
    );

    // Give the lambda function access to the secret
    [getV2SamplesheetUriLambdaObj, findAllFastqPairsInInstrumentRunLambdaObj].forEach(
      (lambda_obj) => {
        icav2AccessTokenSecretObj.grantRead(lambda_obj.currentVersion);
      }
    );

    /*
    Generate an instance of the gzip raw md5sum sfn arn
    */
    const gzipRawMd5sumSingleSfnObj = new GzipRawMd5sumDecompressionConstruct(
      this,
      'gzip_raw_md5sum_single',
      {
        sfnPrefix: `${props.stateMachinePrefix}-gzip`,
        icav2AccessTokenSecretId: icav2AccessTokenSecretObj.secretName,
      }
    ).sfnObject;

    // Create the wrapper that runs this for all fastq files
    const gzipRawMd5sumInstrumentRunScatterSfnObj = new sfn.StateMachine(
      this,
      'gzip_raw_md5sum_run',
      {
        stateMachineName: `${props.stateMachinePrefix}-gzip-raw-md5sum-instrument-run`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            '../step_functions_templates/get_raw_md5sum_for_all_fastq_gzips_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Table */
          __table_name__: dynamodbTableObj.tableName,
          __fastq_list_row_table_partition_name__: this.globals.tablePartitionNames.fastqListRow,
          /* Step functions */
          __gzip_raw_md5sum_sfn_arn__: gzipRawMd5sumSingleSfnObj.stateMachineArn,
        },
      }
    );

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(gzipRawMd5sumInstrumentRunScatterSfnObj);

    // Configure step function invoke access to the gzip raw md5sum sfn
    gzipRawMd5sumSingleSfnObj.grantStartExecution(gzipRawMd5sumInstrumentRunScatterSfnObj);
    gzipRawMd5sumSingleSfnObj.grantRead(gzipRawMd5sumInstrumentRunScatterSfnObj);

    // Allow step function to call nested state machine
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    gzipRawMd5sumInstrumentRunScatterSfnObj.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      gzipRawMd5sumInstrumentRunScatterSfnObj,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    // Generate the rate limit sfn for the gzip raw md5sum sfn
    const gzipRawMd5sumRateLimitSfnObj = new sfn.StateMachine(
      this,
      'rate_limit_get_raw_md5sums_gzip_sfn',
      {
        stateMachineName: `${props.stateMachinePrefix}-rate-limit-gzip-raw-md5sum-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            '../step_functions_templates/rate_limit_get_raw_md5sum_for_fastq_gzip_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Step functions */
          __instrument_run_gzip_to_md5_sfn_arn__:
            gzipRawMd5sumInstrumentRunScatterSfnObj.stateMachineArn,
        },
      }
    );

    // Configure step function to have listexecutions access to the gzip raw md5sum sfn
    gzipRawMd5sumInstrumentRunScatterSfnObj.grantRead(gzipRawMd5sumRateLimitSfnObj);

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      gzipRawMd5sumRateLimitSfnObj,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    /*
    Generate the inputs sfn
    */
    const configureInputsSfn = new sfn.StateMachine(this, 'configure_inputs_sfn', {
      stateMachineName: `${props.stateMachinePrefix}-configure-inputs-json`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/set_compression_inputs.asl.json')
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: dynamodbTableObj.tableName,
        __fastq_list_row_table_partition_name__: this.globals.tablePartitionNames.fastqListRow,
        __instrument_run_id_table_partition_name__:
          this.globals.tablePartitionNames.instrumentRunId,
        /* SSM Parameters */
        __reference_uri_ssm_parameter_path__: referenceUriSsmObj.parameterName,
        /* Lambda Functions */
        __get_v2_samplesheets_uri_lambda_function_arn__:
          getV2SamplesheetUriLambdaObj.currentVersion.functionArn,
        __find_fastq_pairs_lambda_function_arn__:
          findAllFastqPairsInInstrumentRunLambdaObj.currentVersion.functionArn,
        /* Step functions */
        __rate_limit_get_raw_md5sums_gzip_sfn_arn__: gzipRawMd5sumRateLimitSfnObj.stateMachineArn,
        __get_raw_md5sums_for_fastq_gzip_pair_sfn_arn__:
          gzipRawMd5sumInstrumentRunScatterSfnObj.stateMachineArn,
      },
    });

    // Configure inputs step function needs to read-write to the dynamodb table
    dynamodbTableObj.grantReadWriteData(configureInputsSfn);

    // Configure step function allow read access to the ssm parameter path
    referenceUriSsmObj.grantRead(configureInputsSfn);

    // Configure the step function to have invoke access to the lambda functions
    [getV2SamplesheetUriLambdaObj, findAllFastqPairsInInstrumentRunLambdaObj].forEach(
      (lambda_obj) => {
        lambda_obj.currentVersion.grantInvoke(configureInputsSfn);
      }
    );

    // Configure step functions invoke access to the gzip raw md5sum sfn
    [gzipRawMd5sumRateLimitSfnObj, gzipRawMd5sumInstrumentRunScatterSfnObj].forEach((sfnObj) => {
      sfnObj.grantStartExecution(configureInputsSfn);
      sfnObj.grantRead(configureInputsSfn);
    });

    // Configure the step function to have invoke access to the gzip raw md5sum sfn
    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    configureInputsSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      configureInputsSfn,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

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
        memorySize: 1024,
        timeout: Duration.seconds(300),
      }
    );

    // Generate the merge file sizes lambda (used by both the outputs json and the fastq list row compression events)
    const setMergeRgidsLambdaObj = new PythonFunction(this, 'set_merge_rgids_lambda_obj', {
      runtime: Runtime.PYTHON_3_12,
      entry: path.join(__dirname, '../lambdas/merge_rgids_with_fastq_list_rows_py'),
      architecture: Architecture.ARM_64,
      handler: 'handler',
      index: 'merge_rgids_with_fastq_list_rows.py',
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
      },
      timeout: Duration.seconds(120),
      memorySize: 1024,
    });

    // Give the lambda function access to the secret
    icav2AccessTokenSecretObj.grantRead(setMergeRgidsLambdaObj.currentVersion);

    // Give the lambda function access to the secret
    icav2AccessTokenSecretObj.grantRead(setOutputsJsonLambdaFunctionObj.currentVersion);

    // Generate an ora decompression construct
    const oraDecompressionSfn = new OraDecompressionConstruct(this, 'ora_decompression', {
      sfnPrefix: `${props.stateMachinePrefix}-ora`,
      icav2AccessTokenSecretId: icav2AccessTokenSecretObj.secretName,
    }).sfnObject;

    // Create the wrapper that runs this for all fastq files
    const oraRawMd5sumInstrumentRunScatterSfnObj = new sfn.StateMachine(
      this,
      'ora_raw_md5sum_run',
      {
        stateMachineName: `${props.stateMachinePrefix}-ora-raw-md5sum-instrument-run`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            '../step_functions_templates/get_raw_md5sum_for_all_fastq_ora_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Table */
          __table_name__: dynamodbTableObj.tableName,
          __fastq_list_row_table_partition_name__: this.globals.tablePartitionNames.fastqListRow,
          __instrument_run_id_table_partition_name__:
            this.globals.tablePartitionNames.instrumentRunId,
          /* Lambdas */
          __merge_fastq_list_csv_with_rgid_lambda_function_arn__:
            setMergeRgidsLambdaObj.currentVersion.functionArn,
          /* Step functions */
          __ora_validation_sfn_arn__: oraDecompressionSfn.stateMachineArn,
        },
      }
    );

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(oraRawMd5sumInstrumentRunScatterSfnObj);

    // Configure step function invoke access to the lambda function
    setMergeRgidsLambdaObj.currentVersion.grantInvoke(oraRawMd5sumInstrumentRunScatterSfnObj);

    // Configure step function invoke access to the ora raw md5sum sfn
    oraDecompressionSfn.grantStartExecution(oraRawMd5sumInstrumentRunScatterSfnObj);
    oraDecompressionSfn.grantRead(oraRawMd5sumInstrumentRunScatterSfnObj);

    // Allow step function to call nested state machine
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    oraRawMd5sumInstrumentRunScatterSfnObj.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      oraRawMd5sumInstrumentRunScatterSfnObj,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    // Generate the rate limit sfn for the ora raw md5sum sfn
    const oraRawMd5sumRateLimitSfnObj = new sfn.StateMachine(
      this,
      'rate_limit_get_raw_md5sums_ora_sfn',
      {
        stateMachineName: `${props.stateMachinePrefix}-rate-limit-ora-raw-md5sum-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            '../step_functions_templates/rate_limit_get_raw_md5sum_for_fastq_ora_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Step functions */
          __instrument_run_ora_to_md5_sfn_arn__:
            oraRawMd5sumInstrumentRunScatterSfnObj.stateMachineArn,
        },
      }
    );

    // Configure step function to have listexecutions access to the ora raw md5sum sfn
    oraRawMd5sumInstrumentRunScatterSfnObj.grantRead(oraRawMd5sumRateLimitSfnObj);

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      oraRawMd5sumRateLimitSfnObj,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    // Generate outputs
    const configureOutputsSfn = new sfn.StateMachine(this, 'configure_outputs_sfn', {
      stateMachineName: `${props.stateMachinePrefix}-configure-outputs-json`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/set_compression_outputs.asl.json')
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: dynamodbTableObj.tableName,
        __portal_run_id_table_partition_name__: this.globals.tablePartitionNames.portalRunId,
        /* Lambdas */
        __set_outputs_json_lambda_function_arn__:
          setOutputsJsonLambdaFunctionObj.currentVersion.functionArn,
        /* Step functions */
        __rate_limit_get_raw_md5sums_ora_sfn_arn__: oraRawMd5sumRateLimitSfnObj.stateMachineArn,
        __get_raw_md5sums_for_fastq_ora_pair_sfn_arn__:
          oraRawMd5sumInstrumentRunScatterSfnObj.stateMachineArn,
      },
    });

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(configureOutputsSfn);

    // Configure step function invoke access to the lambda function
    setOutputsJsonLambdaFunctionObj.currentVersion.grantInvoke(configureOutputsSfn);

    // Configure step function invoke access to the ora raw md5sum sfn rate limiter
    // And to the ora raw md5sum sfn
    [oraRawMd5sumInstrumentRunScatterSfnObj, oraRawMd5sumRateLimitSfnObj].forEach((sfnObj) => {
      sfnObj.grantStartExecution(configureOutputsSfn);
      sfnObj.grantRead(configureOutputsSfn);
    });

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    configureOutputsSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      configureOutputsSfn,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

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

    /*
    Part 3 - add on service to collect outputs from the succeeded v2 workflow and generate the fastq list row compression events
    */

    // Add the get file sizes lambda function
    const getFileSizesLambdaObj = new PythonFunction(this, 'get_file_sizes_lambda', {
      runtime: Runtime.PYTHON_3_12,
      entry: path.join(__dirname, '../lambdas/get_file_size_from_uri_py'),
      architecture: Architecture.ARM_64,
      handler: 'handler',
      index: 'get_file_size_from_uri.py',
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
      },
      memorySize: 1024,
      timeout: Duration.seconds(300),
    });

    // Give the lambda function access to the secret
    icav2AccessTokenSecretObj.grantRead(getFileSizesLambdaObj.currentVersion);

    // Generate the state machine for generating the fastq list row compression events
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
          /* Tables */
          __table_name__: dynamodbTableObj.tableName,
          __instrument_run_table_partition_name__: this.globals.tablePartitionNames.instrumentRunId,
          __fastq_list_row_table_partition_name__: this.globals.tablePartitionNames.fastqListRow,
          /* Event Bus */
          __event_bus_name__: eventBusObj.eventBusName,
          __detail_type__: this.globals.outputCompressionDetailType,
          /* Lambdas */
          __get_file_size_lambda_function_arn__: getFileSizesLambdaObj.currentVersion.functionArn,
        },
      }
    );

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(generateFastqListRowCompressionEventsSfn);

    // Configure step function invoke access to the lambda function
    getFileSizesLambdaObj.currentVersion.grantInvoke(generateFastqListRowCompressionEventsSfn);

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
