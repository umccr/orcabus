import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailConstruct } from '../../../../../../../../components/event-workflowmanager-workflowrunstatechange-parse-external-event-detail';

/*
Create an event rule for the bclconvertmanager source,
where a workflowrunstatechange detail type has occurred and the workflow is in the succeeded state.

Parse the outputs from the event into a new event object with a different source (workflowrunmanager)

The event output payload will be of the same construct.

Input Event Source: `orcabus.bclconvertmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `succeeded`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

*/

export interface BclconvertManagerEventHandlerConstructProps {
  eventBusObj: events.EventBus;
  tableObj: dynamodb.ITableV2;
}

export class BclconvertSuccessEventRelayer extends Construct {
  public declare bclconvertSuccessEventMap: {
    prefix: 'bclconvertSuccessEventRelayer';
    tablePartition: 'bclconvert_success_event';
    triggerSource: 'orcabus.bclconvertmanager';
    triggerStatus: 'succeeded';
  };

  constructor(scope: Construct, id: string, props: BclconvertManagerEventHandlerConstructProps) {
    super(scope, id);

    /*
        Part 1
        Parse the outputs from the event into a new event object with a different source (workflowrunmanager)

        The event output payload will be of the same construct.

        Input Event Source: `orcabus.bclconvertmanager`
        Input Event DetailType: `orcabus.workflowrunstatechange`
        Input Event status: `succeeded`

        Output Event source: `orcabus.workflowrunmanager`
        Output Event DetailType: `orcabus.workflowrunstatechange`
        Output Event status: `complete`
        */

    /*
        Create the event detail construct
        */
    new WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailConstruct(
      this,
      'bclconvertSuccessEventRelayer',
      {
        lambdaPrefix: this.bclconvertSuccessEventMap.prefix,
        stateMachinePrefix: this.bclconvertSuccessEventMap.prefix,
        tableObj: props.tableObj,
        tablePartitionName: this.bclconvertSuccessEventMap.tablePartition,
        triggerSource: this.bclconvertSuccessEventMap.triggerSource,
        triggerStatus: this.bclconvertSuccessEventMap.triggerStatus,
        eventBusObj: props.eventBusObj,
      }
    );
  }
}
