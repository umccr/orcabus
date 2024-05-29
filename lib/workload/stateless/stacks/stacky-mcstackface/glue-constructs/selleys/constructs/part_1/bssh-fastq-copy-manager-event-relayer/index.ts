import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailConstruct } from '../../../../../../../../components/event-workflowmanager-workflowrunstatechange-parse-external-event-detail';

/*
Create an event rule for the bsshfastqcopymanager source,
where a workflowrunstatechange detail type has occurred and the workflow is in the succeeded state.

Parse the outputs from the event into a new event object with a different source (workflowmanager)

The event output payload will be of the same construct.

Input Event Source: `orcabus.bsshfastqcopymanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `succeeded`

Output Event source: `orcabus.workflowmanager`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `complete`

*/

export interface BSSHFastqCopyManagerEventHandlerConstructProps {
  eventBusObj: events.IEventBus;
  tableObj: dynamodb.ITableV2;
}

export class BSSHFastqCopyManagerEventRelayer extends Construct {
  public readonly bsshFastqCopySuccessEventMap = {
    prefix: 'bsshFastqCopySuccessEventRelayer',
    tablePartition: 'bssh_fastq_copy_event',
    triggerSource: 'orcabus.bsshfastqcopymanager',
    triggerStatus: 'succeeded'
  };

  constructor(scope: Construct, id: string, props: BSSHFastqCopyManagerEventHandlerConstructProps) {
    super(scope, id);

    /*
        Part 1
        Parse the outputs from the event into a new event object with a different source (workflowmanager)

        The event output payload will be of the same construct.

        Input Event Source: `orcabus.bsshfastqcopymanager`
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
      'bsshFastqSuccessEventRelayer',
      {
        lambdaPrefix: this.bsshFastqCopySuccessEventMap.prefix,
        stateMachinePrefix: this.bsshFastqCopySuccessEventMap.prefix,
        tableObj: props.tableObj,
        tablePartitionName: this.bsshFastqCopySuccessEventMap.tablePartition,
        triggerSource: this.bsshFastqCopySuccessEventMap.triggerSource,
        triggerStatus: this.bsshFastqCopySuccessEventMap.triggerStatus,
        eventBusObj: props.eventBusObj,
      }
    );
  }
}
