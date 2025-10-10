import { Construct } from 'constructs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from 'path';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { NagSuppressions } from 'cdk-nag';
import { EventField } from 'aws-cdk-lib/aws-events';

export interface WfmWorkflowStateChangeIcav2ReadyEventHandlerConstructProps {
  /* Names of table to write to */
  tableName: string; // Name of the table to get / update / query

  /* Names of the stateMachine to create */
  stateMachineName: string; // Name of the state machine to create

  /* The type of workflow we're working with */
  workflowPlatformType: string; // One of 'cwl' or 'nextflow'

  /* The pipeline ID ssm parameter path */
  pipelineIdSsmPath: string; // Name of the pipeline id ssm parameter path we want to use as a backup

  /* The ICAV2 Access token (needed to launch the pipeline inside the lambda) */
  icav2AccessTokenSecretObj: secretsmanager.ISecret;

  /* Event configurations to push to  */
  detailType: string; // Detail type of the event to raise
  eventBusName: string; // Detail of the eventbus to push the event to
  triggerLaunchSource: string; // Source of the event that triggers the launch event
  internalEventSource: string; // What we push back to the orcabus

  /* State machines to run (underneath) */
  /* The inputs generation statemachine */
  generateInputsJsonSfn: sfn.IStateMachine;

  /* Internal workflowRunStateChange event details */
  workflowName: string;
  workflowVersion: string;
  serviceVersion: string;

  /* Extras (all optional) */
  analysisStorageSize?: string;
}

export class WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct extends Construct {
  public readonly stateMachineObj: sfn.StateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: WfmWorkflowStateChangeIcav2ReadyEventHandlerConstructProps
  ) {
    super(scope, id);

    // Get table object
    const table_obj = dynamodb.TableV2.fromTableName(this, 'table_obj', props.tableName);

    // Get the event bus object
    const eventbus_obj = events.EventBus.fromEventBusName(
      this,
      'orcabus_eventbus_obj',
      props.eventBusName
    );

    // Build the launch lambda object
    const launch_lambda_obj = new lambda_python.PythonFunction(
      this,
      'icav2_cwl_launch_python_function',
      {
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        entry: path.join(__dirname, 'icav2_launch_pipeline_lambda_py'),
        index: 'icav2_launch_pipeline_lambda.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(300),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretArn,
        },
      }
    );

    // Give the lambda the ability to read the icav2 secret
    props.icav2AccessTokenSecretObj.grantRead(launch_lambda_obj);

    // Collect the pipeline id from the ssm parameter store
    const pipeline_id_ssm_param_obj = ssm.StringParameter.fromStringParameterName(
      this,
      'pipeline_id_ssm_param_obj',
      props.pipelineIdSsmPath
    );

    // Build state machine object
    this.stateMachineObj = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: props.stateMachineName,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates/icav2_launch_workflow_and_raise_internal_event.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Table object */
        __table_name__: table_obj.tableName,
        /* Workflow Platform type */
        __workflow_platform_type__: props.workflowPlatformType, // One of 'cwl' or 'nextflow'
        /* Event metadata */
        __detail_type__: props.detailType,
        __eventbus_name__: props.eventBusName,
        __event_source__: props.internalEventSource,
        /* Put event details */
        __workflow_type__: props.workflowName,
        __workflow_version__: props.workflowVersion,
        __service_version__: props.serviceVersion,
        /* Lambdas */
        __launch_icav2_pipeline_lambda_function_name__:
          launch_lambda_obj.currentVersion.functionArn,
        __analysis_storage_size__: props.analysisStorageSize || 'SMALL',
        /* SSM Parameter paths */
        __pipeline_id_ssm_path__: pipeline_id_ssm_param_obj.parameterName,
        /* Step functions */
        __set_input_json_state_machine_arn__: props.generateInputsJsonSfn.stateMachineArn,
      },
    });

    /* Grant the state machine access to invoke the launch lambda function */
    launch_lambda_obj.currentVersion.grantInvoke(this.stateMachineObj);

    /* Grant the state machine access to the ssm parameter path */
    pipeline_id_ssm_param_obj.grantRead(this.stateMachineObj);

    // Grant the state machine the ability to start the internal generate inputs sfn
    props.generateInputsJsonSfn.grantStartExecution(this.stateMachineObj);
    props.generateInputsJsonSfn.grantRead(this.stateMachineObj);

    /* Grant the state machine access to invoke the internal launch sfn machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    this.stateMachineObj.addToRolePolicy(
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
      this.stateMachineObj,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    /* Grant the state machine read and write access to the table */
    table_obj.grantReadWriteData(this.stateMachineObj);

    // Create a rule for this state machine
    const rule = new events.Rule(this, 'rule', {
      eventBus: eventbus_obj,
      ruleName: `${props.stateMachineName}-rule`,
      eventPattern: {
        source: [props.triggerLaunchSource],
        detailType: [props.detailType],
        detail: {
          status: ['READY'],
          workflow: {
            name: [{ 'equals-ignore-case': props.workflowName }],
            version: [{ 'equals-ignore-case': props.workflowVersion }],
          },
        },
      },
    });

    // Add target of event to be the state machine
    // But revert to a legacy event type for the target
    rule.addTarget(
      new events_targets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromObject({
          status: EventField.fromPath('$.detail.status'),
          timestamp: EventField.fromPath('$.detail.timestamp'),
          workflowName: EventField.fromPath('$.detail.workflow.name'),
          workflowVersion: EventField.fromPath('$.detail.workflow.version'),
          workflowRunName: EventField.fromPath('$.detail.workflowRunName'),
          portalRunId: EventField.fromPath('$.detail.portalRunId'),
          linkedLibraries: EventField.fromPath('$.detail.libraries'),
          payload: EventField.fromPath('$.detail.payload'),
        }),
      })
    );

    /* Grant the state machine the ability to submit events to the event bus */
    eventbus_obj.grantPutEventsTo(this.stateMachineObj);
  }
}
