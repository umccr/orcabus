/*
Workflow Step Functions Sync Manager

Allow a step function to wait while a workflow completes

*/

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { StateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';

export interface WorkflowTaskTokenManagerConfig {
  /*
  Tables
  */
  dynamodbTableName: string;

  /*
  Event handling
  */
  eventBusName: string;

  /*
  Names for statemachines
  */
  stateMachinePrefix: string;
}

export type WorkflowTaskTokenManagerStackProps = WorkflowTaskTokenManagerConfig & cdk.StackProps;

export class WorkflowTaskTokenManagerStack extends cdk.Stack {
  private globals = {
    source: 'orcabus.workflowsync',
    triggerDetailType: 'WorkflowRunStateChangeSync',
    outputDetailType: 'WorkflowRunStateChange',
    tablePartitionName: 'portal_run_id_task_token',
  };

  private createLaunchWorkflowRunStateChangeStepFunction(
    eventBusObj: IEventBus,
    tableObj: dynamodb.ITableV2,
    stateMachineName: string
  ): StateMachine {
    /*
    Build the state machine
    */
    const stateMachineObj = new sfn.StateMachine(this, stateMachineName, {
      stateMachineName: stateMachineName,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../step_functions_templates/launch_workflow_run_state_change_event.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: tableObj.tableName,
        __portal_run_id_table_partition_name__: this.globals.tablePartitionName,
        /* Events */
        __detail_type__: this.globals.triggerDetailType,
        __event_bus_name__: eventBusObj.eventBusName,
        __source__: this.globals.source,
      },
    });

    // Give state machine permissions to read/write to db
    tableObj.grantReadWriteData(stateMachineObj);

    // Give state machine permissions to put events to event bus
    eventBusObj.grantPutEventsTo(stateMachineObj);

    // Return state machine
    return stateMachineObj;
  }

  private createSendTaskTokenStepFunction(
    eventBusObj: IEventBus,
    tableObj: dynamodb.ITableV2,
    stateMachineName: string
  ): StateMachine {
    const stateMachineObj = new sfn.StateMachine(this, stateMachineName, {
      stateMachineName: stateMachineName,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/send_task_token.asl.json')
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: tableObj.tableName,
        __portal_run_id_table_partition_name__: this.globals.tablePartitionName,
        /* Events */
        __detail_type__: this.globals.triggerDetailType,
        __event_bus_name__: eventBusObj.eventBusName,
        __source__: this.globals.source,
      },
    });

    // Grant permissions to read/write data
    tableObj.grantReadWriteData(stateMachineObj);

    // Return the state machine object
    return stateMachineObj;
  }

  private createRuleForWorkflowRunStateChangeSyncEvents(
    eventBusObj: events.IEventBus,
    ruleName: string
  ): events.Rule {
    /*
    Can't use $or over detailType and detail so use two rules instead
    */
    return new events.Rule(this, ruleName, {
      eventBus: eventBusObj,
      ruleName: ruleName,
      eventPattern: {
        detailType: [this.globals.triggerDetailType],
        detail: {
          portalRunId: { exists: true },
          taskToken: { exists: true },
        },
      },
    });
  }

  private createRuleForWorkflowRunStateChangeEvents(
    eventBusObj: events.IEventBus,
    ruleName: string
  ): events.Rule {
    /*
    Can't use $or over detailType and detail so use two rules instead
    */
    return new events.Rule(this, ruleName, {
      eventBus: eventBusObj,
      ruleName: ruleName,
      eventPattern: {
        detailType: [this.globals.outputDetailType],
        detail: {
          portalRunId: { exists: true },
          // One of SUCCEEDED, ABORTED, FAILED, DEPRECATED
          status: [
            { 'equals-ignore-case': 'SUCCEEDED' },
            { 'equals-ignore-case': 'FAILED' },
            { 'equals-ignore-case': 'ABORTED' },
            { 'equals-ignore-case': 'DEPRECATED' },
          ],
        },
      },
    });
  }

  constructor(scope: Construct, id: string, props: WorkflowTaskTokenManagerStackProps) {
    super(scope, id, props);

    // Get dynamodb table for construct
    const tableObj = dynamodb.TableV2.fromTableName(this, 'tableObj', props.dynamodbTableName);

    // Get the event bus object
    const eventBusObj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Add launch workflow run state change step function object
    const launchWorkflowRunStateChangeSfnObj = this.createLaunchWorkflowRunStateChangeStepFunction(
      eventBusObj,
      tableObj,
      `${props.stateMachinePrefix}-launch-state-machine-sfn`
    );

    // Add send task token state change step function object
    const sendTaskTokenStateChangeSfnObj = this.createSendTaskTokenStepFunction(
      eventBusObj,
      tableObj,
      `${props.stateMachinePrefix}-send-task-token-sfn`
    );

    // Rules
    const workflowRunStateChangeLaunchRule = this.createRuleForWorkflowRunStateChangeSyncEvents(
      eventBusObj,
      'workflow-sync-launch-wrsc-rule'
    );

    const sendTaskTokenLaunchRule = this.createRuleForWorkflowRunStateChangeEvents(
      eventBusObj,
      'workflow-sync-send-task-token-event-rule'
    );

    // Add targets to rules
    workflowRunStateChangeLaunchRule.addTarget(
      new eventsTargets.SfnStateMachine(launchWorkflowRunStateChangeSfnObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    // Add the target to the task token rule
    sendTaskTokenLaunchRule.addTarget(
      new events_targets.SfnStateMachine(sendTaskTokenStateChangeSfnObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
