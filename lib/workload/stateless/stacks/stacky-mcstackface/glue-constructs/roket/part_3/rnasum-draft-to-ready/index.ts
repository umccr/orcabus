import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/event-workflowdraftrunstatechange-to-workflowrunstatechange-ready';

/*
Part 5

Input Event source: `orcabus.rnasuminputeventglue`
Input Event DetailType: `WorkflowDraftRunStateChange`
Input Event status: `draft`

Output Event source: `orcabus.rnasuminputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The rnasumInputMaker, subscribes to the rnasum input event glue (itself) and generates a ready event for the rnasumReadySfn
  * However, in order to be 'READY' we need to use a few more variables such as
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference
*/

export interface RnasumInputMakerConstructProps {
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

export class RnasumInputMakerConstruct extends Construct {
  public readonly rnasumInputMakerEventMap = {
    prefix: 'roket-rnasum',
    tablePartition: 'rnasum',
    triggerSource: 'orcabus.rnasuminputeventglue',
    triggerStatus: 'DRAFT',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    outputSource: 'orcabus.rnasuminputeventglue',
    outputStatus: 'READY',
    payloadVersion: '2024.07.16',
    workflowName: 'rnasum',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: RnasumInputMakerConstructProps) {
    super(scope, id);

    /*
    Part 3: Build the external sfn
    */
    new WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct(
      this,
      'rnasum_internal_input_maker',
      {
        /*
        Set Input StateMachine Object
        */
        lambdaPrefix: this.rnasumInputMakerEventMap.prefix,
        payloadVersion: this.rnasumInputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.rnasumInputMakerEventMap.prefix,
        rulePrefix: `stacky-${this.rnasumInputMakerEventMap.prefix}`,

        /*
        Table objects
        */
        tableObj: props.inputMakerTableObj,
        tablePartitionName: this.rnasumInputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerDetailType: this.rnasumInputMakerEventMap.triggerDetailType,
        triggerSource: this.rnasumInputMakerEventMap.triggerSource,
        triggerStatus: this.rnasumInputMakerEventMap.triggerStatus,
        outputSource: this.rnasumInputMakerEventMap.outputSource,
        workflowName: this.rnasumInputMakerEventMap.workflowName,
        workflowVersion: this.rnasumInputMakerEventMap.workflowVersion,

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
