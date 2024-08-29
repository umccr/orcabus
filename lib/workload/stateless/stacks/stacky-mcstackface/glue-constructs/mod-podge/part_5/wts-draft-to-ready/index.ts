import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/event-workflowdraftrunstatechange-to-workflowrunstatechange-ready';

/*
Part 5

Input Event source: `orcabus.wtsinputeventglue`
Input Event DetailType: `WorkflowDraftRunStateChange`
Input Event status: `draft`

Output Event source: `orcabus.wtsinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The wtsInputMaker, subscribes to the wts input event glue (itself) and generates a ready event for the wtsReadySfn
  * However, in order to be 'READY' we need to use a few more variables such as
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference
*/

export interface WtsInputMakerConstructProps {
  /* Event bus object */
  eventBusObj: events.IEventBus;
  /* Tables */
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameter Objects */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class WtsInputMakerConstruct extends Construct {
  public readonly wtsInputMakerEventMap = {
    prefix: 'modpodge-wts',
    tablePartition: 'wts',
    triggerSource: 'orcabus.wtsinputeventglue',
    triggerStatus: 'DRAFT',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    outputSource: 'orcabus.wtsinputeventglue',
    outputStatus: 'READY',
    payloadVersion: '2024.07.16',
    workflowName: 'wts',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: WtsInputMakerConstructProps) {
    super(scope, id);

    /*
    Part 3: Build the external sfn
    */
    new WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct(
      this,
      'wts_internal_input_maker',
      {
        /*
        Set Input StateMachine Object
        */
        lambdaPrefix: this.wtsInputMakerEventMap.prefix,
        payloadVersion: this.wtsInputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.wtsInputMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.inputMakerTableObj,
        tablePartitionName: this.wtsInputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerDetailType: this.wtsInputMakerEventMap.triggerDetailType,
        triggerSource: this.wtsInputMakerEventMap.triggerSource,
        triggerStatus: this.wtsInputMakerEventMap.triggerStatus,
        outputSource: this.wtsInputMakerEventMap.outputSource,
        workflowName: this.wtsInputMakerEventMap.workflowName,
        workflowVersion: this.wtsInputMakerEventMap.workflowVersion,

        /*
        SSM Parameter Objects
        */
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,

        /*
        Secrets
        */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
      }
    );
  }
}
