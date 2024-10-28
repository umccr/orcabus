import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { BsshFastqCopyManagerReadyMakerConstruct } from './part_1/bclconvert-succeeded-to-bssh-fastq-copy';
import { NestedStack } from 'aws-cdk-lib/core';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface BclconvertToBsshFastqCopyEventHandlerConstructProps {
  /* Event Bus */
  eventBusObj: events.IEventBus;

  /* SSM Parameter */
  bsshOutputFastqCopyUriSsmParameterObj: ssm.IStringParameter;

  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class BclconvertToBsshFastqCopyEventHandlerConstruct extends NestedStack {
  constructor(
    scope: Construct,
    id: string,
    props: BclconvertToBsshFastqCopyEventHandlerConstructProps
  ) {
    super(scope, id);
    /*
    Part 1
    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `complete`

    Output Event Source: `orcabus.bclconvertmanagerinputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`

    * The BsshFastqCopyManagerInputMaker Construct
      * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
      * Generates the portal run id and submits a draft event
    */
    const bclconvertToBsshFastqCopyDraftMaker = new BsshFastqCopyManagerReadyMakerConstruct(
      this,
      'bclconvert_to_bssh_fastq_copy_draft_maker',
      {
        /* Event Bus handler */
        eventBusObj: props.eventBusObj,
        /* ICAv2 Secret */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
        /* Output URI SSM Configuration Obj */
        outputUriSsmParameterObj: props.bsshOutputFastqCopyUriSsmParameterObj,
      }
    );
  }
}
