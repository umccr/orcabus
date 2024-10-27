import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { BclconvertInteropQcDraftMakerConstruct } from './part_1/bclconvert-interop-qc-draft-event-maker';
import { NestedStack } from 'aws-cdk-lib/core';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface BsshFastqCopyToBclconvertInteropQcConstructProps {
  /* Event Objects */
  eventBusObj: events.IEventBus;
  /* SSM Parameter Ojbects */
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class BsshFastqCopyToBclconvertInteropQcConstruct extends NestedStack {
  constructor(
    scope: Construct,
    id: string,
    props: BsshFastqCopyToBclconvertInteropQcConstructProps
  ) {
    super(scope, id);

    /*
    Part 1

    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `complete`
    Input Event WorkflowName: `bsshFastqCopy`

    Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `READY`

    * The BCLConvertInteropQCInputMaker Construct
      * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
      * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter
    */
    const bsshFastqCopyCompleteToBclConvertInteropQcDraft =
      new BclconvertInteropQcDraftMakerConstruct(
        this,
        'bssh_fastq_copy_complete_to_bclconvert_interop_qc_draft_maker',
        {
          /* Event Bus */
          eventBusObj: props.eventBusObj,
          /* SSM Parameter Objects */
          logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
          outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
          icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
          /* Secrets Manager */
          icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
        }
      );
  }
}
