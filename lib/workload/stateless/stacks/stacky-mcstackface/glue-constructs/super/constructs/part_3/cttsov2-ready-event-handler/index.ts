import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailConstruct } from '../../../../../../../../components/event-workflowmanager-workflowrunstatechange-parse-external-event-detail';

/*
* Input Event Source: `orcabus.cttsov2inputeventglue`
* Input Event DetailType: `WorkflowRunStateChange`
* Input Event status: `complete`

* Output Event source: `orcabus.workflowmanager`
* Output Event DetailType: `WorkflowRunStateChange`
* Output Event status: `ready`

* The ctTSOv2ReadyEventSubmitter Construct
  * Subscribes to the ctTSOv2InputMaker Construct outputs and generates a ready event for the ctTSOv2ReadySfn
*/

export interface cttsov2ManagerReadyEventHandlerConstructProps {
  eventBusObj: events.IEventBus;
  tableObj: dynamodb.ITableV2;
}

export class cttsov2ManagerReadyEventHandlerConstruct extends Construct {
  public readonly cttsov2ReadyEventMap = {
    prefix: 'cttsov2ReadyEventRelayer',
    tablePartition: 'cttsov2_ready_event',
    triggerSource: 'orcabus.cttsov2inputeventglue',
    triggerStatus: 'ready',
  };

  constructor(scope: Construct, id: string, props: cttsov2ManagerReadyEventHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1
    Parse the outputs from the event into a new event object with a different source (workflowmanager)

    The event output payload will be of the same construct.

    Input Event Source: `orcabus.bclconvertmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `succeeded`

    Output Event source: `orcabus.workflowmanager`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `complete`
    */

    /*
    Create the event detail construct
    */
    new WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailConstruct(
      this,
      'bclconvertSuccessEventRelayer',
      {
        lambdaPrefix: this.cttsov2ReadyEventMap.prefix,
        stateMachinePrefix: this.cttsov2ReadyEventMap.prefix,
        tableObj: props.tableObj,
        tablePartitionName: this.cttsov2ReadyEventMap.tablePartition,
        triggerSource: this.cttsov2ReadyEventMap.triggerSource,
        triggerStatus: this.cttsov2ReadyEventMap.triggerStatus,
        eventBusObj: props.eventBusObj,
      }
    );
  }
}
