/*
SFN NF Batch Ready event wrapper

This wrapper will run an AWS step function and connect your ready event, to AWS batch.
*/

import { Construct } from 'constructs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from 'path';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as batch from 'aws-cdk-lib/aws-batch';

export interface WfmWorkflowStateChangeNfBatchStateChangeEventHandlerConstructProps {
  /* Names of table to write to */
  tableObj: dynamodb.ITableV2; // Name of the table to get / update / query

  /* Names of the stateMachine to create */
  stateMachinePrefix: string; // Name of the state machine to create

  /* Event configurations to push to */
  eventBusObj: events.IEventBus; // Detail of the eventbus to push the event to
  detailType: string; // Detail type of the event to raise
  triggerLaunchSource: string; // Source of the event that triggers the launch event
  internalEventSource: string; // What we push back to the orcabus

  /* State machines to run (underneath) */
  /* The Batch generation statemachine */
  generateBatchOutputsLambdaObj: lambda_python.PythonFunction; // The lambda object to run to generate the batch

  /* Batch details */
  batchJobDefinitionObj: batch.IJobDefinition; // The job definition to run

  /* Internal workflowRunStateChange event details */
  workflowName: string;
  workflowVersion: string;
}

export class WfmWorkflowStateChangeNfBatchStateChangeEventHandlerConstruct extends Construct {
  public readonly stateMachineObj: sfn.StateMachine;
  private readonly globals = {
    defaultEventBusName: 'default',
    eventStatus: 'SUBMITTED',
    portalRunTablePartitionName: 'portal_run_id',
    eventDetailType: 'WorkflowRunStateChange',
    serviceVersion: '2024.10.17'
  }

  constructor(
    scope: Construct,
    id: string,
    props: WfmWorkflowStateChangeNfBatchStateChangeEventHandlerConstructProps
  ) {
    super(scope, id);

    // Get the default AWS event bus as this is where
    // Batch pushes events to
    const defaultEventBus = events.EventBus.fromEventBusName(
      this,
      'default-event-bus',
      this.globals.defaultEventBusName
    );

    // Build state machine object
    this.stateMachineObj = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: `${props.stateMachinePrefix}-wfm-nf-batch-state-change-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates/capture_aws_batch_completion_events_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Table object */
        __table_name__: props.tableObj.tableName,
        /* Table Partitions */
        __portal_run_table_partition_name: this.globals.portalRunTablePartitionName,
        /* Event metadata */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_detail_type__: this.globals.eventDetailType,
        __event_detail_version__: this.globals.serviceVersion,
        __event_source__: props.internalEventSource,
        __event_status__: this.globals.eventStatus,
        /* Workflow details */
        __workflow_name__: props.workflowName,
        __workflow_version__: props.workflowVersion,
        /* Lambdas */
        __generate_outputs_lambda_function_arn__: props.generateBatchOutputsLambdaObj.currentVersion.functionArn,
      },
    });

    /* Grant the state machine access to invoke the launch lambda function */
    props.generateBatchOutputsLambdaObj.currentVersion.grantInvoke(this.stateMachineObj);

    /* Grant the state machine read and write access to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    // Create a rule for this state machine
    const rule = new events.Rule(this, 'rule', {
      eventBus: defaultEventBus,
      ruleName: `${props.stateMachinePrefix}-rule`,
      eventPattern: {
        source: [props.triggerLaunchSource],
        detailType: [props.detailType],
        detail: {
          jobDefinition: [{ 'equals-ignore-case': props.batchJobDefinitionObj.jobDefinitionArn }],
        },
      },
    });

    /* Add rule as a target to the state machine */
    rule.addTarget(
      new events_targets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    /* Grant the state machine the ability to submit events to the event bus */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);
  }
}
