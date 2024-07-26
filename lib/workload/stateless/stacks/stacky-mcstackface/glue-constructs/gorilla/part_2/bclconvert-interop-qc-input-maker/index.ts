import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/event-workflowdraftrunstatechange-to-workflowrunstatechange-ready';

/*
Part 1

* Input Event Source: `orcabus.bclconvertinteropqcinputeventglue`
* Input Event DetailType: `WorkflowDraftRunStateChange`
* Input Event WorkflowName: bclconvertInteropQc
* Input Event status: `draft`

* Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
* Output Event DetailType: `WorkflowRunStateChange`
* Output Event status: `ready`


* The bclconvertInteropQcDraftToReady Construct
  * Subscribes to the bclconvert draft maker Stack outputs and creates the input for the BCLConvert Interop QC Pipeline
*/

export interface bclconvertInteropQcDraftToReadyMakerConstructProps {
  tableObj: dynamodb.ITableV2;
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  eventBusObj: events.IEventBus;
}

export class BclconvertInteropQcDraftToReadyMakerConstruct extends Construct {
  public readonly bclconvertInteropQcDraftToReadyMakerEventMap = {
    prefix: 'gorilla-interop-qc',
    tablePartition: 'bclconvert_interop_qc',
    triggerSource: 'orcabus.bclconvertinteropqcinputeventglue',
    triggerStatus: 'draft',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    outputSource: 'orcabus.bclconvertinteropqcinputeventglue',
    outputStatus: 'ready',
    payloadVersion: '2024.05.24',
    workflowName: 'bclconvertInteropQc',
    workflowVersion: '2024.05.24',
  };

  constructor(
    scope: Construct,
    id: string,
    props: bclconvertInteropQcDraftToReadyMakerConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Initialise the workflow draft run state change to workflow run state change construct
    */
    new WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct(
      this,
      'bclconvert_interop_qc_draft_to_ready_sfn',
      {
        /*
        Set Input StateMachine Object
        */
        lambdaPrefix: this.bclconvertInteropQcDraftToReadyMakerEventMap.prefix,
        payloadVersion: this.bclconvertInteropQcDraftToReadyMakerEventMap.payloadVersion,
        stateMachinePrefix: this.bclconvertInteropQcDraftToReadyMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.tableObj,
        tablePartitionName: this.bclconvertInteropQcDraftToReadyMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerSource: this.bclconvertInteropQcDraftToReadyMakerEventMap.triggerSource,
        triggerStatus: this.bclconvertInteropQcDraftToReadyMakerEventMap.triggerStatus,

        /*
        Event Outputs
        */
        workflowName: this.bclconvertInteropQcDraftToReadyMakerEventMap.workflowName,
        workflowVersion: this.bclconvertInteropQcDraftToReadyMakerEventMap.workflowVersion,
        outputSource: this.bclconvertInteropQcDraftToReadyMakerEventMap.outputSource,

        /*
        Set the output uri
        */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      }
    );
  }
}
