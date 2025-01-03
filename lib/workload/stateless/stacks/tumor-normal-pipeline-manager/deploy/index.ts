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
import { WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct } from '../../../../components/sfn-icav2-ready-event-handler';
import { Icav2AnalysisEventHandlerConstruct } from '../../../../components/sfn-icav2-state-change-event-handler';
import { OraDecompressionConstruct } from '../../../../components/ora-file-decompression-fq-pair-sfn';
import { NagSuppressions } from 'cdk-nag';

export interface TnIcav2PipelineManagerConfig {
  /* ICAv2 Pipeline analysis essentials */
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pipelineIdSsmPath: string; // List of parameters the workflow session state machine will need access to
  referenceUriSsmPath: string; // "/icav2/umccr-prod/reference-genome-uri"
  oraReferenceUriSsmPath: string; // "/icav2/umccr-prod/ora-reference-uri-ssm-path"
  defaultReferenceVersion: string;
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

export type TnIcav2PipelineManagerStackProps = TnIcav2PipelineManagerConfig & cdk.StackProps;

export class TnIcav2PipelineManagerStack extends cdk.Stack {
  private readonly dynamodbTableObj: dynamodb.ITableV2;
  private readonly icav2AccessTokenSecretObj: secretsManager.ISecret;
  private readonly eventBusObj: events.IEventBus;
  private readonly pipelineIdSsmObj: ssm.IStringParameter;

  constructor(scope: Construct, id: string, props: TnIcav2PipelineManagerStackProps) {
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
    this.pipelineIdSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.pipelineIdSsmPath,
      props.pipelineIdSsmPath
    );

    // Set annotation and reference ssm objects
    const referenceSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.referenceUriSsmPath,
      props.referenceUriSsmPath
    );
    const oraReferenceSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.oraReferenceUriSsmPath,
      props.oraReferenceUriSsmPath
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
    const addOraReferenceLambdaObj = new PythonFunction(
      this,
      'add_ora_reference_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/add_ora_reference_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'add_ora_reference.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
      }
    );

    // Get the ora decompression construct
    const oraDecompressionStateMachineObj = new OraDecompressionConstruct(
      this,
      'ora_decompression_state_machine_obj',
      {
        icav2AccessTokenSecretId: this.icav2AccessTokenSecretObj.secretName,
        sfnPrefix: `${props.stateMachinePrefix}-ora-to-gz`,
      }
    ).sfnObject;

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const configureInputsSfn = new sfn.StateMachine(
      this,
      'tn_v2_launch_step_functions_state_machine',
      {
        stateMachineName: `${props.stateMachinePrefix}-configure-inputs-json`,
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(
          path.join(__dirname, '../step_functions_templates/', 'set_tn_cwl_inputs_sfn.asl.json')
        ),
        // definitionSubstitutions
        definitionSubstitutions: {
          /* Dynamodb tables */
          __table_name__: this.dynamodbTableObj.tableName,
          /* SSM Parameters */
          __reference_version_uri_ssm_parameter_name__: referenceSsmObj.parameterName,
          __ora_reference_uri_ssm_parameter_path__: oraReferenceSsmObj.parameterName,
          __default_reference_version__: props.defaultReferenceVersion,
          // We collect the reference version AND the pipeline versions
          /* Lambdas */
          __convert_fastq_list_rows_lambda_function_arn__:
            convertFastqListRowsToCwlInputObjectsLambdaObj.currentVersion.functionArn,
          __get_boolean_parameters_lambda_function_arn__:
            getBooleanParametersFromEventInputLambdaObj.currentVersion.functionArn,
          __add_ora_reference_lambda_function_arn__:
            addOraReferenceLambdaObj.currentVersion.functionArn,
          /* Step functions */
          __ora_fastq_list_row_decompression_sfn_arn__:
            oraDecompressionStateMachineObj.stateMachineArn,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    [
      convertFastqListRowsToCwlInputObjectsLambdaObj,
      getBooleanParametersFromEventInputLambdaObj,
      addOraReferenceLambdaObj,
    ].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(configureInputsSfn);
    });

    // Allow state machine to read/write to dynamodb table
    this.dynamodbTableObj.grantReadWriteData(configureInputsSfn);

    // Allow state machine to read ssm parameters
    [referenceSsmObj, oraReferenceSsmObj].forEach((ssmObj) => {
      ssmObj.grantRead(configureInputsSfn);
    });

    // Allow state machine to invoke the ora decompression state machine
    oraDecompressionStateMachineObj.grantStartExecution(configureInputsSfn);
    oraDecompressionStateMachineObj.grantRead(configureInputsSfn);

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
    this.icav2AccessTokenSecretObj.grantRead(setOutputJsonLambdaObj.currentVersion);

    const configureOutputsSfn = new sfn.StateMachine(this, 'sfn_configure_outputs_json', {
      stateMachineName: `${props.stateMachinePrefix}-configure-outputs-json`,
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates', 'set_tn_cwl_outputs_sfn.asl.json')
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
    new WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct(this, 'tn_wfm_sfn_handler', {
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
      'handle_tn_ready_event',
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
