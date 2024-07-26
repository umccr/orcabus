import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import * as iam from 'aws-cdk-lib/aws-iam';
import path from 'path';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';
import { PythonLambdaFastqListRowsToCwlInputConstruct } from '../../../../components/python-lambda-fastq-list-rows-to-cwl-input';
import { WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct } from '../../../../components/dynamodb-icav2-ready-event-handler-sfn';
import { Icav2AnalysisEventHandlerConstruct } from '../../../../components/dynamodb-icav2-handle-event-change-sfn';

export interface WtsIcav2PipelineManagerConfig {
  /* ICAv2 Pipeline analysis essentials */
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pipelineIdSsmPath: string; // List of parameters the workflow session state machine will need access to
  dragenReferenceUriSsmPath: string; // "/icav2/umccr-prod/reference-genome-uri"
  fastaReferenceUriSsmPath: string; // "/icav2/umccr-prod/reference-genome-uri" // FIXME
  gencodeAnnotationUriSsmPath: string; // "/icav2/umccr-prod/gencode-annotation-uri" // FIXME
  arribaUriSsmPath: string; // "/icav2/umccr-prod/arriba-uri" // FIXME
  wtsQcReferenceSamplesSsmPath: string; // "/icav2/umccr-prod/wts-qc-reference-samples" // FIXME
  /* Defaults */
  defaultDragenReferenceVersion: string; // v9-r3
  defaultFastaReferenceVersion: string; // hg38
  defaultGencodeAnnotationVersion: string; // v39
  defaultArribaVersion: string; // 2.4.0
  defaultQcReferenceSamplesVersion: string; // 2023-07-21--4.2.4
  /* Table to store analyis metadata */
  dynamodbTableName: string;
  /* Internal and external buses */
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

export type WtsIcav2PipelineManagerStackProps = WtsIcav2PipelineManagerConfig & cdk.StackProps;

export class WtsIcav2PipelineManagerStack extends cdk.Stack {
  private readonly dynamodbTableObj: dynamodb.ITableV2;
  private readonly icav2AccessTokenSecretObj: secretsManager.ISecret;
  private readonly eventBusObj: events.IEventBus;
  private readonly pipelineIdSsmObj: ssm.IStringParameter;

  constructor(scope: Construct, id: string, props: WtsIcav2PipelineManagerStackProps) {
    super(scope, id, props);

    // Get dynamodb table for construct
    this.dynamodbTableObj = dynamodb.TableV2.fromTableName(
      this,
      'dynamodb_table',
      props.dynamodbTableName
    );

    // Get ICAv2 Access token secret object for construct
    this.icav2AccessTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'icav2_secrets_object',
      props.icav2TokenSecretId
    );

    // Set ssm parameter objects
    // Pipeline
    this.pipelineIdSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.pipelineIdSsmPath,
      props.pipelineIdSsmPath
    );

    // Dragen Reference
    const dragenReferenceSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.dragenReferenceUriSsmPath,
      props.dragenReferenceUriSsmPath
    );

    // Fasta Reference
    const fastaReferenceSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.fastaReferenceUriSsmPath,
      props.fastaReferenceUriSsmPath
    );

    // Annotation
    const annotationSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.gencodeAnnotationUriSsmPath,
      props.gencodeAnnotationUriSsmPath
    );

    // Arriba
    const arribaSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.arribaUriSsmPath,
      props.arribaUriSsmPath
    );

    // WTS QC Reference Samples
    const wtsQcReferenceSamplesSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.wtsQcReferenceSamplesSsmPath,
      props.wtsQcReferenceSamplesSsmPath
    );

    // Get event bus object
    this.eventBusObj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    /*
    Build lambdas
    */

    // Convert Fastq List Rows to Lambda Object
    const convertFastqListRowsToCwlInputObjectsLambdaObj =
      new PythonLambdaFastqListRowsToCwlInputConstruct(
        this,
        'convert_fastq_list_rows_to_cwl_input_objects_lambda'
      ).lambdaObj;

    const getBooleanParametersFromEventInputLambdaObj = new PythonFunction(
      this,
      'get_boolean_parameters_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/get_boolean_parameters_from_event_input_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_boolean_parameters_from_event_input.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
      }
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const configureInputsSfn = new sfn.StateMachine(
      this,
      'wts_v2_launch_step_functions_state_machine',
      {
        stateMachineName: `${props.stateMachinePrefix}-configure-inputs-json`,
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(
          path.join(__dirname, '../step_functions_templates/', 'set_wts_cwl_inputs_sfn.asl.json')
        ),
        // definitionSubstitutions
        definitionSubstitutions: {
          /* Dynamodb tables */
          __table_name__: this.dynamodbTableObj.tableName,
          /* SSM Parameters */
          __reference_version_uri_ssm_parameter_name__: dragenReferenceSsmObj.parameterName,
          __reference_fasta_version_uri_ssm_parameter_name__: fastaReferenceSsmObj.parameterName,
          __arriba_version_uri_ssm_parameter_name__: arribaSsmObj.parameterName,
          __annotation_version_uri_ssm_parameter_name__: annotationSsmObj.parameterName,
          __qc_reference_samples_version_uri_ssm_parameter_name__:
            wtsQcReferenceSamplesSsmObj.parameterName,

          /* Defaults */
          __default_reference_version__: props.defaultDragenReferenceVersion,
          __default_reference_fasta_version__: props.defaultFastaReferenceVersion,
          __default_annotation_version__: props.defaultGencodeAnnotationVersion,
          __default_arriba_version__: props.defaultArribaVersion,
          __default_qc_reference_samples_version__: props.defaultQcReferenceSamplesVersion,
          // We collect the reference version AND the pipeline versions
          /* Lambdas */
          __convert_fastq_list_rows_lambda_function_arn__:
            convertFastqListRowsToCwlInputObjectsLambdaObj.currentVersion.functionArn,
          __get_boolean_parameters_lambda_function_arn__:
            getBooleanParametersFromEventInputLambdaObj.currentVersion.functionArn,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    [
      convertFastqListRowsToCwlInputObjectsLambdaObj,
      getBooleanParametersFromEventInputLambdaObj,
    ].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(configureInputsSfn);
    });

    // Allow state machine to read/write to dynamodb table
    this.dynamodbTableObj.grantReadWriteData(configureInputsSfn);

    // Allow state machine to read ssm parameters
    [
      dragenReferenceSsmObj,
      fastaReferenceSsmObj,
      arribaSsmObj,
      annotationSsmObj,
      wtsQcReferenceSamplesSsmObj,
    ].forEach((ssmObj) => {
      ssmObj.grantRead(configureInputsSfn);
    });

    /*
    Part 2: Configure the lambdas and outputs step function
    Quite a bit more complicated than regular ICAv2 workflow setup since we need to
    1. Generate the outputs json from a nextflow pipeline (which doesn't have a json outputs endpoint)
    2. Delete the cache fastqs we generated in the configure inputs json step function
    */

    // Build the lambdas
    // Set the output json lambda
    const setOutputJsonLambdaObj = new PythonFunction(
      this,
      'set_output_json_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/set_outputs_json_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'set_outputs_json.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: this.icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    // Add permissions to lambda
    this.icav2AccessTokenSecretObj.grantRead(<iam.IRole>setOutputJsonLambdaObj.currentVersion.role);

    const configureOutputsSfn = new sfn.StateMachine(this, 'sfn_configure_outputs_json', {
      stateMachineName: `${props.stateMachinePrefix}-configure-outputs-json`,
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates', 'set_wts_cwl_outputs_sfn.asl.json')
      ),
      // definitionSubstitutions
      definitionSubstitutions: {
        /* Dynamodb tables */
        __table_name__: this.dynamodbTableObj.tableName,
        __set_outputs_json_lambda_function_arn__: setOutputJsonLambdaObj.currentVersion.functionArn,
      },
    });

    // Allow the state machine to read/write to dynamodb table
    this.dynamodbTableObj.grantReadWriteData(configureOutputsSfn);

    // Allow the state machine to invoke the lambda
    setOutputJsonLambdaObj.currentVersion.grantInvoke(configureOutputsSfn);

    /* Add ICAv2 WfmworkflowRunStateChange wrapper around launch state machine */
    // This state machine handles the event target configurations */
    new WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct(this, 'wts_wfm_sfn_handler', {
      /* Names of objects to get */
      tableName: this.dynamodbTableObj.tableName, // Name of the table to get / update / query
      /* Workflow type */
      workflowPlatformType: 'cwl', // This is a cwl pipeline
      icav2AccessTokenSecretObj: this.icav2AccessTokenSecretObj, // Secret to get the icav2 access token
      /* Names of objects to create */
      stateMachineName: `${props.stateMachinePrefix}-wfm-ready-event-handler`, // Name of the state machine to create
      /* The pipeline ID ssm parameter path */
      pipelineIdSsmPath: this.pipelineIdSsmObj.parameterName, // Name of the pipeline id ssm parameter path we want to use as a backup
      /* Event configurations to push to  */
      detailType: props.detailType, // Detail type of the event to raise
      eventBusName: this.eventBusObj.eventBusName, // Detail of the eventbus to push the event to
      triggerLaunchSource: props.triggerLaunchSource, // Source of the event that triggers the launch event
      internalEventSource: props.internalEventSource, // What we push back to the orcabus
      /* State machines to run (underneath) */
      /* The inputs generation statemachine */
      generateInputsJsonSfn: configureInputsSfn,
      /* Internal workflowRunStateChange event details */
      workflowName: props.workflowType,
      workflowVersion: props.workflowVersion,
      serviceVersion: props.serviceVersion,
    });

    // Create statemachine for handling any state changes of the pipeline
    // Generate state machine for handling the external ICAv2 event
    const handleExternalIcav2Sfn = new Icav2AnalysisEventHandlerConstruct(
      this,
      'handle_wts_ready_event',
      {
        // Table stuff
        tableName: this.dynamodbTableObj.tableName,
        // Miscell stuff
        stateMachineName: `${props.stateMachinePrefix}-icav2-external-handler`,
        /* Event things */
        eventBusName: this.eventBusObj.eventBusName,
        detailType: props.detailType,
        icaEventPipeName: props.icaEventPipeName,
        workflowName: props.workflowType,
        workflowVersion: props.workflowVersion,
        internalEventSource: props.internalEventSource,
        serviceVersion: props.serviceVersion,
        /* Pipeline stuff */
        generateOutputsJsonSfn: configureOutputsSfn,
      }
    ).stateMachineObj;
  }
}
