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
  eventBusObj: events.EventBus;
  tableObj: dynamodb.ITableV2;
}

export class BclconvertInteropqcManagerReadyEventHandlerConstruct extends Construct {
  public declare bsshFastqCopyReadyEventMap: {
    prefix: 'bsshFastqCopyReadyEventRelayer';
    tablePartition: 'bssh_fastq_copy_ready_event';
    triggerSource: 'orcabus.bsshfastqcopyinputeventglue';
    triggerStatus: 'ready';
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
        lambdaPrefix: this.bsshFastqCopyReadyEventMap.prefix,
        stateMachinePrefix: this.bsshFastqCopyReadyEventMap.prefix,
        tableObj: props.tableObj,
        tablePartitionName: this.bsshFastqCopyReadyEventMap.tablePartition,
        triggerSource: this.bsshFastqCopyReadyEventMap.triggerSource,
        triggerStatus: this.bsshFastqCopyReadyEventMap.triggerStatus,
        eventBusObj: props.eventBusObj,
      }
    );
  }
}
