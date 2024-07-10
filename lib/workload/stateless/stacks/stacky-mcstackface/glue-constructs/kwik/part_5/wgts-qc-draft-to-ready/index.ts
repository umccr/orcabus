import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/event-workflowdraftrunstatechange-to-workflowrunstatechange-ready';

/*
Part 5

Input Event source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: `WorkflowDraftRunStateChange`
Input Event status: `draft`

Output Event source: `orcabus.wgtsqcinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The wgtsQcInputMaker, subscribes to the wgtsqc input event glue (itself) and generates a ready event for the wgtsqcReadySfn
  * For the cttso v2 workflow we require a samplesheet, a set of fastq list rows (provided in the last step)
  * However, in order to be 'ready' we need to use a few more variables such as
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference
*/

export interface WgtsQcInputMakerConstructProps {
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

export class WgtsQcInputMakerConstruct extends Construct {
  public readonly wgtsQcInputMakerEventMap = {
    prefix: 'wgtsQcInputMaker',
    tablePartition: 'wgts_qc',
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'draft',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    outputSource: 'orcabus.wgtsqcinputeventglue',
    outputStatus: 'ready',
    payloadVersion: '2024.05.24',
    workflowName: 'wgtsQc',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: WgtsQcInputMakerConstructProps) {
    super(scope, id);

    /*
    Part 3: Build the external sfn
    */
    new WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct(
      this,
      'wgts_qc_copy_manager_internal_input_maker',
      {
        /*
        Set Input StateMachine Object
        */
        lambdaPrefix: this.wgtsQcInputMakerEventMap.prefix,
        payloadVersion: this.wgtsQcInputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.wgtsQcInputMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.inputMakerTableObj,
        tablePartitionName: this.wgtsQcInputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerDetailType: this.wgtsQcInputMakerEventMap.triggerDetailType,
        triggerSource: this.wgtsQcInputMakerEventMap.triggerSource,
        triggerStatus: this.wgtsQcInputMakerEventMap.triggerStatus,
        outputSource: this.wgtsQcInputMakerEventMap.outputSource,
        workflowName: this.wgtsQcInputMakerEventMap.workflowName,
        workflowVersion: this.wgtsQcInputMakerEventMap.workflowVersion,

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
