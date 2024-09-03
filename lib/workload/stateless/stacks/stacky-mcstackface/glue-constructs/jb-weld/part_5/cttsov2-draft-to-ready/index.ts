import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/event-workflowdraftrunstatechange-to-workflowrunstatechange-ready';

/*
Part 5

Input Event source: `orcabus.cttsov2inputeventglue`
Input Event DetailType: `WorkflowDraftRunStateChange`
Input Event status: `draft`

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The ctTSOv2InputMaker, subscribes to the cttsov2 input event glue (itself) and generates a ready event for the ctTSOv2ReadySfn
  * For the cttso v2 workflow we require a samplesheet, a set of fastq list rows (provided in the last step)
  * However, in order to be 'READY' we need to use a few more variables such as
    * icaLogsUri,
    * analysisOutputUri
    * cacheUri
    * projectId
    * userReference
*/

export interface Cttsov2InputMakerConstructProps {
  /* Event bus object */
  eventBusObj: events.IEventBus;
  /* Tables */
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameter Objects */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
  /* Secrets Objects */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class Cttsov2InputMakerConstruct extends Construct {
  public readonly cttsov2InputMakerEventMap = {
    prefix: 'jbweld-cttso-v2',
    tablePartition: 'cttso_v2',
    triggerSource: 'orcabus.cttsov2inputeventglue',
    triggerStatus: 'DRAFT',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    triggerWorkflowName: 'cttsov2',
    outputSource: 'orcabus.cttsov2inputeventglue',
    outputStatus: 'READY',
    payloadVersion: '2024.05.24',
    workflowName: 'cttsov2',
    workflowVersion: '2.6.0',
  };

  constructor(scope: Construct, id: string, props: Cttsov2InputMakerConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the draft to ready maker
    */
    new WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct(
      this,
      'cttso_v2_draft_to_ready_sfn',
      {
        /*
        Set Input StateMachine Object
        */
        lambdaPrefix: this.cttsov2InputMakerEventMap.prefix,
        payloadVersion: this.cttsov2InputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.cttsov2InputMakerEventMap.prefix,
        rulePrefix: this.cttsov2InputMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.inputMakerTableObj,
        tablePartitionName: this.cttsov2InputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerDetailType: this.cttsov2InputMakerEventMap.triggerDetailType,
        triggerSource: this.cttsov2InputMakerEventMap.triggerSource,
        triggerStatus: this.cttsov2InputMakerEventMap.triggerStatus,
        outputSource: this.cttsov2InputMakerEventMap.outputSource,
        workflowName: this.cttsov2InputMakerEventMap.workflowName,
        workflowVersion: this.cttsov2InputMakerEventMap.workflowVersion,

        /*
        SSM Parameters
        */
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /*
        Secrets
        */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
      }
    );
  }
}
