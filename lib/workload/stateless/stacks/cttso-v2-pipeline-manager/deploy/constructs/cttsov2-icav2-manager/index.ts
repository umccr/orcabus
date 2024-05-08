import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Icav2AnalysisEventHandlerConstruct } from '../../../../../../components/dynamodb-icav2-handle-event-change-sfn';

interface Cttsov2Icav2ManagerConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;
  icav2AccessTokenSecretObj: secretsManager.ISecret;
  lambdaLayerObj: lambda.ILayerVersion;
  icav2CopyBatchStateMachineObj: sfn.IStateMachine;
  pipelineIdSSMParameterObj: ssm.IStringParameter; // List of parameters the workflow session state machine will need access to
  eventbusObj: events.IEventBus;
  /* Lambdas paths */
  generateDbUuidLambdaPath: string; // __dirname + '/../../../lambdas/generate_db_uuid'
  generateTrimmedSamplesheetLambdaPath: string; // __dirname + '/../../../lambdas/generate_trimmed_samplesheet_lambda_path'
  uploadSamplesheetToCacheDirLambdaPath: string; // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
  generateCopyManifestDictLambdaPath: string; // __dirname + '/../../../lambdas/generate_copy_manifest_dict'
  launchCttsov2NextflowPipelineLambdaPath: string; // __dirname + '/../../../lambdas/launch_cttso_nextflow_pipeline'
  /* Step function templates */
  workflowDefinitionBodyPath: string; // __dirname + '/../../../step_functions_templates/cttso_v2_launch_step_function.json'
  /* Event bus parameters */
  workflowType: string; // The workflow type cttso_v2
  workflowVersion: string; // The workflow version (2.1.1)
  serviceVersion: string; // The service version (2024.05.07)
}

export class Cttsov2Icav2PipelineManagerConstruct extends Construct {
  public readonly cttsov2LaunchStateMachineName: string;
  public readonly cttsov2LaunchStateMachineArn: string;

  public readonly cttsov2CaptureIcav2EventsStateMachineName: string;
  public readonly cttsov2CaptureIcav2EventsStateMachineArn: string;

  constructor(scope: Construct, id: string, props: Cttsov2Icav2ManagerConstructProps) {
    super(scope, id);

    // launch_cttso_nextflow_pipeline lambda
    const launch_cttso_nextflow_pipeline_lambda_obj = new PythonFunction(
      this,
      'launch_cttso_nextflow_pipeline_lambda_python_function',
      {
        entry: props.launchCttsov2NextflowPipelineLambdaPath,
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
      <iam.IRole>launch_cttso_nextflow_pipeline_lambda_obj.role
    );

    // Add each of the ssm parameters to the lambda role policy
    props.pipelineIdSSMParameterObj.grantRead(
      <iam.IRole>launch_cttso_nextflow_pipeline_lambda_obj.role
    );

    // generate_db_uuid_lambda_path lambda
    // Doesnt need any ssm parameters
    const generate_db_uuid_lambda_obj = new PythonFunction(
      this,
      'generate_db_uuid_lambda_python_function',
      {
        entry: props.generateDbUuidLambdaPath,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdaLayerObj],
        timeout: Duration.seconds(60),
      }
    );

    // generate_copy_manifest_dict lambda
    // Doesnt need any ssm parameters
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
      <iam.IRole>upload_samplesheet_to_cache_dir_lambda_obj.role
    );

    // Add each of the ssm parameters to the lambda role policy
    props.pipelineIdSSMParameterObj.grantRead(
      <iam.IRole>upload_samplesheet_to_cache_dir_lambda_obj.role
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(
      this,
      'cttso_v2_launch_step_functions_state_machine',
      {
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(props.workflowDefinitionBodyPath),
        // definitionSubstitutions
        definitionSubstitutions: {
          /* Lambda arns */
          __generate_db_uuid__: generate_db_uuid_lambda_obj.functionArn,
          __launch_cttso_nextflow_pipeline__: launch_cttso_nextflow_pipeline_lambda_obj.functionArn,
          __generate_copy_manifest_dict__: generate_copy_manifest_dict_lambda_obj.functionArn,
          __generate_trimmed_samplesheet__: generate_trimmed_samplesheet_lambda_obj.functionArn,
          __upload_samplesheet_to_cache_dir__:
            upload_samplesheet_to_cache_dir_lambda_obj.functionArn,
          /* Subfunction state machines */
          __copy_batch_data_state_machine_arn__:
            props.icav2CopyBatchStateMachineObj.stateMachineArn,
          /* Dynamodb tables */
          __table_name__: props.dynamodbTableObj.tableName,
          /* Event bus to push to */
          __eventbus_name__: props.eventbusObj.eventBusName,
          /* Event bus parameters */
          __workflow_type__: props.workflowType,
          __workflow_version__: props.workflowVersion,
          __service_version_: props.serviceVersion,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    [
      generate_db_uuid_lambda_obj,
      launch_cttso_nextflow_pipeline_lambda_obj,
      generate_copy_manifest_dict_lambda_obj,
      generate_trimmed_samplesheet_lambda_obj,
      upload_samplesheet_to_cache_dir_lambda_obj,
    ].forEach((lambda_obj) => {
      lambda_obj.currentVersion.grantInvoke(<iam.IRole>stateMachine.role);
    });

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(stateMachine.role);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Add state machine execution permissions to stateMachine role
    props.icav2CopyBatchStateMachineObj.grantStartExecution(stateMachine.role);

    // Trigger state machine on event
    const rule = new events.Rule(this, 'cttso_v2_launch_step_function_rule', {
      eventBus: props.eventbusObj,
      eventPattern: {
        source: ['orcabus.wfm'],
        detailType: ['workflowRunStateChange'],
        /*
        FIXME - nothing is set in stone yet
        */
        detail: {
          status: ['ready'],
          workflow: ['cttso_v2_launch'],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new events_targets.SfnStateMachine(stateMachine, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    // Allow the statemachine to submit events to the event bus
    props.eventbusObj.grantPutEventsTo(stateMachine.role);

    // Create statemachine for handling any state changes of the pipeline
    const statechange_statemachine = new Icav2AnalysisEventHandlerConstruct(
      this,
      'cttso_icav2_statechange_handler',
      {
        // Table name //
        tableName: props.dynamodbTableObj.tableName,
        // Name of future statemachine
        stateMachineName: 'cttsov2Icav2StateChangeHandlerSfn',
        // Statemachine substitutions we need to pass
        eventBusName: props.eventbusObj.eventBusName,
        source: 'orcabus.cttso_v2',
        detailType: 'workflowRunStateChange',
        /* Event parameters */
        workflowType: props.workflowType,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      }
    );

    // Set outputs
    this.cttsov2LaunchStateMachineName = stateMachine.stateMachineName;
    this.cttsov2LaunchStateMachineArn = stateMachine.stateMachineArn;

    this.cttsov2CaptureIcav2EventsStateMachineName =
      statechange_statemachine.stateMachineObj.stateMachineName;
    this.cttsov2CaptureIcav2EventsStateMachineArn =
      statechange_statemachine.stateMachineObj.stateMachineArn;
  }
}
