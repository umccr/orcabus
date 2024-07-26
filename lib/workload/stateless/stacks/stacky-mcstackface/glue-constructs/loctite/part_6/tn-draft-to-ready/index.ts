import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/event-workflowdraftrunstatechange-to-workflowrunstatechange-ready';

/*
Part 6

Input Event source: `orcabus.tninputeventglue`
Input Event DetailType: `WorkflowDraftRunStateChange`
Input Event status: `draft`

Output Event source: `orcabus.tninputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The tnInputMaker, subscribes to the tn input event glue (itself) and generates a ready event for the tnReadySfn
  * However, in order to be 'ready' we need to use a few more variables such as
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference
*/

export interface TnInputMakerConstructProps {
  /* Event bus object */
  eventBusObj: events.IEventBus;
  /* Tables */
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameter Objects */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
}

export class TnInputMakerConstruct extends Construct {
  public readonly tnInputMakerEventMap = {
    prefix: 'loctite-tn',
    tablePartition: 'tn',
    triggerSource: 'orcabus.tninputeventglue',
    triggerStatus: 'draft',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    outputSource: 'orcabus.tninputeventglue',
    outputStatus: 'ready',
    payloadVersion: '2024.07.16',
    workflowName: 'tumor_normal',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: TnInputMakerConstructProps) {
    super(scope, id);

    /*
    Part 3: Build the external sfn
    */
    new WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct(
      this,
      'tn_internal_input_maker',
      {
        /*
        Set Input StateMachine Object
        */
        lambdaPrefix: this.tnInputMakerEventMap.prefix,
        payloadVersion: this.tnInputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.tnInputMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.inputMakerTableObj,
        tablePartitionName: this.tnInputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerDetailType: this.tnInputMakerEventMap.triggerDetailType,
        triggerSource: this.tnInputMakerEventMap.triggerSource,
        triggerStatus: this.tnInputMakerEventMap.triggerStatus,
        outputSource: this.tnInputMakerEventMap.outputSource,
        workflowName: this.tnInputMakerEventMap.workflowName,
        workflowVersion: this.tnInputMakerEventMap.workflowVersion,

        /*
        SSM Parameter Objects
        */
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
      }
    );
  }
}
