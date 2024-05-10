import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Icav2AnalysisEventHandlerConstruct } from '../../../../../../components/dynamodb-icav2-handle-event-change-sfn';
import { WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct } from '../../../../../../components/dynamodb-icav2-ready-event-handler-sfn';

interface Cttsov2Icav2PipelineManagerConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;
  icav2AccessTokenSecretObj: secretsManager.ISecret;
  pipelineIdSsmObj: ssm.IStringParameter;
  // Step function generate paths
  generateInputJsonSfnTemplatePath: string; // __dirname + '/../../../step_functions_templates/cttso_v2_launch_step_function.json'
  // Event buses
  eventBusName: string;
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
  // Lambda layers paths
  lambdaLayerObj: lambda.ILayerVersion;
  generateTrimmedSamplesheetLambdaPath: string; // __dirname + '/../../../lambdas/generate_trimmed_samplesheet_lambda_path'
  uploadSamplesheetToCacheDirLambdaPath: string; // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
  generateCopyManifestDictLambdaPath: string; // __dirname + '/../../../lambdas/generate_copy_manifest_dict'
  launchCttsov2NextflowPipelineLambdaPath: string; // __dirname + '/../../../lambdas/launch_cttso_nextflow_pipeline'
  // ICAv2 Copy Batch State Machine Object
  icav2CopyBatchStateMachineObj: sfn.IStateMachine;
}

export class Cttsov2Icav2PipelineManagerConstruct extends Construct {
  public readonly handleWfmReadyEventStateMachineObj: string;
  public readonly handleIcav2EventStateMachineObj: string;

  constructor(scope: Construct, id: string, props: Cttsov2Icav2PipelineManagerConstructProps) {
    super(scope, id);

    /*
    Part 1: Set up the lambdas needed for the input json generation state machine
    Quite a bit more complicated than regular ICAv2 workflow setup since we need to
    1. Update the samplesheet
    2. Copy fastqs into a particular directory setup type
    */

    // generate_copy_manifest_dict lambda
    const generate_copy_manifest_dict_lambda_obj = new PythonFunction(
      this,
      'generate_copy_manifest_dict_lambda_python_function',
      {
        entry: props.generateCopyManifestDictLambdaPath,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdaLayerObj],
        timeout: Duration.seconds(60),
      }
    );

    // Generate trimmed samplesheet lambda
    // Also doesn't need any ssm parameters or secrets
    const generate_trimmed_samplesheet_lambda_obj = new PythonFunction(
      this,
      'generate_trimmed_samplesheet_lambda_python_function',
      {
        entry: props.generateTrimmedSamplesheetLambdaPath,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdaLayerObj],
        timeout: Duration.seconds(60),
      }
    );

    // upload_samplesheet_to_cache_dir lambda
    const upload_samplesheet_to_cache_dir_lambda_obj = new PythonFunction(
      this,
      'upload_samplesheet_to_cache_dir_lambda_python_function',
      {
        entry: props.uploadSamplesheetToCacheDirLambdaPath,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdaLayerObj],
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    // Add icav2 secrets permissions to lambda
    props.icav2AccessTokenSecretObj.grantRead(
      <iam.IRole>upload_samplesheet_to_cache_dir_lambda_obj.currentVersion.role
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const configure_inputs_sfn = new sfn.StateMachine(
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
            generate_copy_manifest_dict_lambda_obj.currentVersion.functionArn,
          __generate_trimmed_samplesheet__:
            generate_trimmed_samplesheet_lambda_obj.currentVersion.functionArn,
          __upload_samplesheet_to_cache_dir__:
            upload_samplesheet_to_cache_dir_lambda_obj.currentVersion.functionArn,
          /* Subfunction state machines */
          __copy_batch_data_state_machine_arn__:
            props.icav2CopyBatchStateMachineObj.stateMachineArn,
          /* Dynamodb tables */
          __table_name__: props.dynamodbTableObj.tableName,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    [
      generate_copy_manifest_dict_lambda_obj,
      generate_trimmed_samplesheet_lambda_obj,
      upload_samplesheet_to_cache_dir_lambda_obj,
    ].forEach((lambda_obj) => {
      lambda_obj.currentVersion.grantInvoke(<iam.IRole>configure_inputs_sfn.role);
    });

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(configure_inputs_sfn.role);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    configure_inputs_sfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Add state machine execution permissions to stateMachine role
    props.icav2CopyBatchStateMachineObj.grantStartExecution(configure_inputs_sfn.role);

    /* Add ICAv2 WfmworkflwoRunStateChange wrapper around launch state machine */
    // This state machine handles the event target configurations */
    const statemachine_launch_wrapper = new WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct(
      this,
      'cttso_v2_wfm_sfn_handler',
      {
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
        eventBusName: props.eventBusName, // Detail of the eventbus to push the event to
        triggerLaunchSource: props.triggerLaunchSource, // Source of the event that triggers the launch event
        internalEventSource: props.internalEventSource, // What we push back to the orcabus
        /* State machines to run (underneath) */
        /* The inputs generation statemachine */
        generateInputsJsonSfn: configure_inputs_sfn,
        /* Internal workflowRunStateChange event details */
        workflowType: props.workflowType,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      }
    );

    // Create statemachine for handling any state changes of the pipeline
    // Generate state machine for handling the external ICAv2 event
    const handle_external_icav2_event_sfn = new Icav2AnalysisEventHandlerConstruct(
      this,
      'handle_interop_qc_ready_event',
      {
        tableName: props.dynamodbTableObj.tableName,
        stateMachineName: `${props.stateMachinePrefix}-icav2-external-handler`,
        detailType: props.detailType,
        eventBusName: props.eventBusName,
        icaEventPipeName: props.icaEventPipeName,
        internalEventSource: props.internalEventSource,
        workflowType: props.workflowType,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      }
    ).stateMachineObj;
  }
}
