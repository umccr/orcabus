import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Icav2AnalysisEventHandlerConstruct } from '../../../../../../components/sfn-icav2-state-change-event-handler';
import { WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct } from '../../../../../../components/sfn-icav2-ready-event-handler';
import { DockerImageFunction } from 'aws-cdk-lib/aws-lambda';

interface Cttsov2Icav2PipelineManagerConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;
  icav2AccessTokenSecretObj: secretsManager.ISecret;
  pipelineIdSsmObj: ssm.IStringParameter;
  // Step function generate paths
  generateInputJsonSfnTemplatePath: string; // __dirname + '/../../../step_functions_templates/cttso_v2_launch_step_function.json'
  generateOutputJsonSfnTemplatePath: string; // __dirname + "../../../step_functions_templates/cttso_v2_output_step_function.json"
  // Event buses
  eventBusObj: events.IEventBus;
  icaEventPipeName: string;
  // Event handling
  workflowType: string;
  workflowVersion: string;
  serviceVersion: string;
  triggerLaunchSource: string;
  internalEventSource: string;
  detailType: string;
  // StateMachineNames
  stateMachinePrefix: string;
  /* Extras */
  // Lambdas
  // SFN Input Lambdas
  uploadSamplesheetToCacheDirLambdaObj: PythonFunction;
  generateCopyManifestDictLambdaObj: PythonFunction;
  checkNumRunningSfnsLambdaObj: PythonFunction;
  getRandomNumberLambdaObj: PythonFunction;
  // SFN Output lambdas
  deleteCacheUriLambdaObj: PythonFunction;
  setOutputJsonLambdaObj: PythonFunction;
  getVcfsLambdaObj: PythonFunction;
  compressVcfLambdaObj: DockerImageFunction;
  checkSuccessSampleLambdaObj: PythonFunction;
  // ICAv2 Copy Batch State Machine Object
  icav2CopyFilesStateMachineObj: sfn.IStateMachine;
}

export class Cttsov2Icav2PipelineManagerConstruct extends Construct {
  // Set the analysis storage size for these runs to LARGE
  private readonly analysisStorageSize = 'LARGE';

  constructor(scope: Construct, id: string, props: Cttsov2Icav2PipelineManagerConstructProps) {
    super(scope, id);

    // Add icav2 secrets permissions to lambdas
    [props.uploadSamplesheetToCacheDirLambdaObj, props.generateCopyManifestDictLambdaObj].forEach(
      (lambda_obj) => {
        props.icav2AccessTokenSecretObj.grantRead(lambda_obj.currentVersion);
      }
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const configureInputsSfn = new sfn.StateMachine(
      this,
      'cttso_v2_launch_step_functions_state_machine',
      {
        stateMachineName: `${props.stateMachinePrefix}-configure-inputs-json`,
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(props.generateInputJsonSfnTemplatePath),
        // definitionSubstitutions
        definitionSubstitutions: {
          /* Lambda arns */
          __generate_copy_manifest_dict__:
            props.generateCopyManifestDictLambdaObj.currentVersion.functionArn,
          __upload_samplesheet_to_cache_dir__:
            props.uploadSamplesheetToCacheDirLambdaObj.currentVersion.functionArn,
          __get_variable_number_of_seconds_lambda_function_arn__:
            props.getRandomNumberLambdaObj.currentVersion.functionArn,
          __check_number_of_copy_jobs_running_lambda_function_arn__:
            props.checkNumRunningSfnsLambdaObj.currentVersion.functionArn,
          /* Subfunction state machines */
          __copy_icav2_files_state_machine_arn__:
            props.icav2CopyFilesStateMachineObj.stateMachineArn,
          /* Dynamodb tables */
          __table_name__: props.dynamodbTableObj.tableName,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    [
      props.generateCopyManifestDictLambdaObj,
      props.uploadSamplesheetToCacheDirLambdaObj,
      props.getRandomNumberLambdaObj,
      props.checkNumRunningSfnsLambdaObj,
    ].forEach((lambda_obj) => {
      lambda_obj.currentVersion.grantInvoke(configureInputsSfn);
    });

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(configureInputsSfn);

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

    // Add state machine execution permissions to stateMachine role
    props.icav2CopyFilesStateMachineObj.grantStartExecution(configureInputsSfn);

    // Update checkNumRunningSfnsLambdaObj env var to include the state machine arn of
    // the icav2 copy files sfn
    props.checkNumRunningSfnsLambdaObj.addEnvironment(
      'SFN_ARN',
      props.icav2CopyFilesStateMachineObj.stateMachineArn
    );

    // Allow the check num running sfns lambda to list the number of running icav2 copy file sfns running
    /*
    // FIXME: this is the ideal setup but not approved by cdk nag, since we
    // FIXME: are granting the lambda permissions to all versions of the step function
    props.icav2CopyFilesStateMachineObj.grantRead(
      props.checkNumRunningSfnsLambdaObj.currentVersion
    );
    */
    props.checkNumRunningSfnsLambdaObj.currentVersion.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'states:ListActivities',
          'states:DescribeStateMachine',
          'states:DescribeActivity',
          'states:ListExecutions',
        ],
        resources: [props.icav2CopyFilesStateMachineObj.stateMachineArn],
      })
    );

    /*
        Part 2: Configure the lambdas and outputs step function
        Quite a bit more complicated than regular ICAv2 workflow setup since we need to
        1. Generate the outputs json from a nextflow pipeline (which doesn't have a json outputs endpoint)
        2. Delete the cache fastqs we generated in the configure inputs json step function
    */

    // Add icav2 secrets permissions to lambdas
    [
      props.deleteCacheUriLambdaObj,
      props.setOutputJsonLambdaObj,
      props.getVcfsLambdaObj,
      props.compressVcfLambdaObj,
      props.checkSuccessSampleLambdaObj,
    ].forEach((lambda_obj) => {
      props.icav2AccessTokenSecretObj.grantRead(lambda_obj.currentVersion);
    });

    const configureOutputsSfn = new sfn.StateMachine(this, 'sfn_configure_outputs_json', {
      stateMachineName: `${props.stateMachinePrefix}-configure-outputs-json`,
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.generateOutputJsonSfnTemplatePath),
      // definitionSubstitutions
      definitionSubstitutions: {
        /* Dynamodb tables */
        __table_name__: props.dynamodbTableObj.tableName,
        __delete_cache_uri_lambda_function_arn__:
          props.deleteCacheUriLambdaObj.currentVersion.functionArn,
        __set_outputs_json_lambda_function_arn__:
          props.setOutputJsonLambdaObj.currentVersion.functionArn,
        __find_all_vcf_files_lambda_function_arn__:
          props.getVcfsLambdaObj.currentVersion.functionArn,
        __compress_vcf_file_lambda_function_arn__:
          props.compressVcfLambdaObj.currentVersion.functionArn,
        __check_successful_analysis_lambda_function_arn__:
          props.checkSuccessSampleLambdaObj.currentVersion.functionArn,
      },
    });

    // Allow the state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(configureOutputsSfn);

    // Allow the state machine to invoke the lambdas
    [
      props.deleteCacheUriLambdaObj,
      props.setOutputJsonLambdaObj,
      props.getVcfsLambdaObj,
      props.compressVcfLambdaObj,
      props.checkSuccessSampleLambdaObj,
    ].forEach((lambda_obj) => {
      lambda_obj.currentVersion.grantInvoke(configureOutputsSfn);
    });

    /* Add ICAv2 WfmworkflowRunStateChange wrapper around launch state machine */
    // This state machine handles the event target configurations */
    new WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct(this, 'cttso_v2_wfm_sfn_handler', {
      /* Names of objects to get */
      tableName: props.dynamodbTableObj.tableName, // Name of the table to get / update / query
      /* Workflow type */
      workflowPlatformType: 'nextflow', // This is a nextflow pipeline
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj, // Secret to get the icav2 access token
      /* Names of objects to create */
      stateMachineName: `${props.stateMachinePrefix}-wfm-ready-event-handler`, // Name of the state machine to create
      /* The pipeline ID ssm parameter path */
      pipelineIdSsmPath: props.pipelineIdSsmObj.parameterName, // Name of the pipeline id ssm parameter path we want to use as a backup
      /* Event configurations to push to  */
      detailType: props.detailType, // Detail type of the event to raise
      eventBusName: props.eventBusObj.eventBusName, // Detail of the eventbus to push the event to
      triggerLaunchSource: props.triggerLaunchSource, // Source of the event that triggers the launch event
      internalEventSource: props.internalEventSource, // What we push back to the orcabus
      /* State machines to run (underneath) */
      /* The inputs generation statemachine */
      generateInputsJsonSfn: configureInputsSfn,
      /* Internal workflowRunStateChange event details */
      workflowName: props.workflowType,
      workflowVersion: props.workflowVersion,
      serviceVersion: props.serviceVersion,
      /* Miscell configurations */
      analysisStorageSize: this.analysisStorageSize,
    });

    // Create statemachine for handling any state changes of the pipeline
    // Generate state machine for handling the external ICAv2 event
    const handleExternalIcav2EventSfn = new Icav2AnalysisEventHandlerConstruct(
      this,
      'handle_interop_qc_ready_event',
      {
        tableName: props.dynamodbTableObj.tableName,
        stateMachineName: `${props.stateMachinePrefix}-icav2-external-handler`,
        detailType: props.detailType,
        eventBusName: props.eventBusObj.eventBusName,
        icaEventPipeName: props.icaEventPipeName,
        internalEventSource: props.internalEventSource,
        generateOutputsJsonSfn: configureOutputsSfn,
        workflowName: props.workflowType,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      }
    ).stateMachineObj;
  }
}
