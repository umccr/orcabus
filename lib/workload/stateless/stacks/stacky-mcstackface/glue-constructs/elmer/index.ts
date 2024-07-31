import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BsshFastqCopyManagerDraftMakerConstruct } from './part_1/bclconvert-succeeded-to-bssh-fastq-copy-draft';
import { BsshFastqCopyManagerDraftToReadyMakerConstruct } from './part_2/bssh-fastq-copy-manager-draft-to-ready';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface BclconvertToBsshFastqCopyEventHandlerConstructProps {
  eventBusObj: events.IEventBus;
  inputMakerTableObj: dynamodb.ITableV2;
  bsshOutputFastqCopyUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class BclconvertToBsshFastqCopyEventHandlerConstruct extends Construct {
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
    const bclconvertToBsshFastqCopyDraftMaker = new BsshFastqCopyManagerDraftMakerConstruct(
      this,
      'bclconvert_to_bssh_fastq_copy_draft_maker',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.inputMakerTableObj,
      }
    );

    /*
    Part 2

    Input Event Source: `orcabus.bclconvertmanagerinputeventglue`
    Input Event DetailType: `WorkflowDraftRunStateChange`
    Input Event status: `draft`

    Output Event source: `orcabus.bclconvertmanagerinputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `ready`

    * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter
    */
    const bsshFastqCopyManagerInputMaker = new BsshFastqCopyManagerDraftToReadyMakerConstruct(
      this,
      'bssh_fastq_copy_input_maker',
      {
        eventBusObj: props.eventBusObj,
        outputUriSsmParameterObj: props.bsshOutputFastqCopyUriSsmParameterObj,
        tableObj: props.inputMakerTableObj,
      }
    );
  }
}
