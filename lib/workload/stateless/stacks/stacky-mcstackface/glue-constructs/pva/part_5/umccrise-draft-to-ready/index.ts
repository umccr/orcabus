import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/event-workflowdraftrunstatechange-to-workflowrunstatechange-ready';

/*
Part 5

Input Event source: `orcabus.umccriseinputeventglue`
Input Event DetailType: `WorkflowDraftRunStateChange`
Input Event status: `draft`

Output Event source: `orcabus.umccriseinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The umccriseInputMaker, subscribes to the umccrise input event glue (itself) and generates a ready event for the umccriseReadySfn
  * However, in order to be 'READY' we need to use a few more variables such as
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference
*/

export interface UmccriseInputMakerConstructProps {
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

export class UmccriseInputMakerConstruct extends Construct {
  public readonly umccriseInputMakerEventMap = {
    prefix: 'pva-umccrise',
    tablePartition: 'umccrise',
    triggerSource: 'orcabus.umccriseinputeventglue',
    triggerStatus: 'DRAFT',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    outputSource: 'orcabus.umccriseinputeventglue',
    outputStatus: 'READY',
    payloadVersion: '2024.07.16',
    workflowName: 'umccrise',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: UmccriseInputMakerConstructProps) {
    super(scope, id);

    /*
    Part 3: Build the external sfn
    */
    new WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct(
      this,
      'umccrise_internal_input_maker',
      {
        /*
        Set Input StateMachine Object
        */
        lambdaPrefix: this.umccriseInputMakerEventMap.prefix,
        payloadVersion: this.umccriseInputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.umccriseInputMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.inputMakerTableObj,
        tablePartitionName: this.umccriseInputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerDetailType: this.umccriseInputMakerEventMap.triggerDetailType,
        triggerSource: this.umccriseInputMakerEventMap.triggerSource,
        triggerStatus: this.umccriseInputMakerEventMap.triggerStatus,
        outputSource: this.umccriseInputMakerEventMap.outputSource,
        workflowName: this.umccriseInputMakerEventMap.workflowName,
        workflowVersion: this.umccriseInputMakerEventMap.workflowVersion,

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
