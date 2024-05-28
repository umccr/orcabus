import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailConstruct } from '../../../../../../../../components/event-workflowmanager-workflowrunstatechange-parse-external-event-detail';

/*
* Input Event Source: `orcabus.bclconvertinteropqcinputeventglue`
* Input Event DetailType: `orcabus.workflowrunstatechange`
* Input Event status: `complete`

* Output Event source: `orcabus.workflowmanager`
* Output Event DetailType: `orcabus.workflowrunstatechange`
* Output Event status: `ready`

* The BCLConvertInteropQCReadyEventSubmitter Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and generates a ready event for the BCLConvertInteropQC

*/

export interface BclconvertInteropqcManagerReadyEventHandlerConstructProps {
  eventBusObj: events.IEventBus;
  tableObj: dynamodb.ITableV2;
}

export class BclconvertInteropqcManagerReadyEventHandlerConstruct extends Construct {
  public readonly bclconvertInteropQcEventMap = {
    prefix: 'bclconvertInteropQcEventRelayer',
    tablePartition: 'bclconvert_interopqc_ready_event',
    triggerSource: 'orcabus.bclconvertinteropqcinputeventglue',
    triggerStatus: 'ready',
  };

  constructor(
    scope: Construct,
    id: string,
    props: BclconvertInteropqcManagerReadyEventHandlerConstructProps
  ) {
    super(scope, id);

    /*
        Part 1
        Parse the outputs from the event into a new event object with a different source (workflowmanager)

        The event output payload will be of the same construct.

        Input Event Source: `orcabus.bclconvertmanager`
        Input Event DetailType: `orcabus.workflowrunstatechange`
        Input Event status: `succeeded`

        Output Event source: `orcabus.workflowmanager`
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
        lambdaPrefix: this.bclconvertInteropQcEventMap.prefix,
        stateMachinePrefix: this.bclconvertInteropQcEventMap.prefix,
        tableObj: props.tableObj,
        tablePartitionName: this.bclconvertInteropQcEventMap.tablePartition,
        triggerSource: this.bclconvertInteropQcEventMap.triggerSource,
        triggerStatus: this.bclconvertInteropQcEventMap.triggerStatus,
        eventBusObj: props.eventBusObj,
      }
    );
  }
}
