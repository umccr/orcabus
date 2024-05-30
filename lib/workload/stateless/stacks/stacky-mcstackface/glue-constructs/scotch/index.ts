import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BclconvertSuccessEventRelayer } from './constructs/part_1/bclconvert-success-event-relayer';
import { updateDataBaseOnNewSamplesheetEventConstruct } from './constructs/part_2/update-database-on-new-samplesheet';
import { bsshFastqCopyManagerInputMakerConstruct } from './constructs/part_3/bssh-fastq-copy-manager-input-maker';
import { BsshFastqCopyManagerReadyEventHandlerConstruct } from './constructs/part_4/bssh-fastq-copy-manager-ready-event-relayer';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface BclconvertManagerEventHandlerConstructProps {
  eventBusObj: events.IEventBus;
  workflowManagerTableObj: dynamodb.ITableV2;
  instrumentRunTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  bsshOutputFastqCopyUriPrefixSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class BclconvertManagerEventHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: BclconvertManagerEventHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1
    Parse the outputs from the event into a new event object with a different source (workflowmanager)

    The event output payload will be of the same construct.

    Input Event Source: `orcabus.bclconvertmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `succeeded`

    Output Event source: `orcabus.workflowmanager`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `complete`
    */
    // const bclconvertSuccessEventRelayer = new BclconvertSuccessEventRelayer(
    //   this,
    //   'bclconvert_success_event_relayer',
    //   {
    //     eventBusObj: props.eventBusObj,
    //     tableObj: props.workflowManagerTableObj,
    //   }
    // );

    /*
    Part 2
    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `complete`

    Output Event source: `orcabus.metadatamanager`
    Output Event DetailType: `InstrumentRunStateChange`
    Output Event status: `libraryrunidsregistered`

    * The UpdateDataBaseOnNewSampleSheet Construct
      * Subscribes to the BCLConvertManagerEventHandler Stack outputs and updates the database:
        * Registers all library run ids in the samplesheet
        * Appends libraryrunids to the library ids in the samplesheet
        * For a given library id, queries the current athena database to collect metadata for the library
          * assay
          * type
          * workflow etc.
    */
    const updateDataBaseOnNewSamplesheet = new updateDataBaseOnNewSamplesheetEventConstruct(
      this,
      'update_database_on_new_samplesheet_construct',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.instrumentRunTableObj,
      }
    );

    /*
    Part 3

    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `complete`

    Output Event source: `orcabus.bclconvertmanagerinputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `complete`

    * The BsshFastqCopyManagerInputMaker Construct
      * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
      * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter
    */
    const bsshFastqCopyManagerInputMaker = new bsshFastqCopyManagerInputMakerConstruct(
      this,
      'bssh_fastq_copy_input_maker',
      {
        eventBusObj: props.eventBusObj,
        outputUriPrefixSsmParameterObj: props.bsshOutputFastqCopyUriPrefixSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        tableObj: props.inputMakerTableObj,
      }
    );

    /*
    Part 4

    Input Event Source: `orcabus.bsshfastqcopymanagerinputeventglue`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `complete`

    Output Event source: `orcabus.workflowmanager`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `ready`

    * The BsshFastqCopyManagerReadyEventSubmitter Construct
      * Subscribes to the BCLConvertManagerEventHandler Stack outputs and generates a ready event for the BSSHFastqCopyManager
    */
    // const bsshFastqCopyReadyEventSubmitter = new BsshFastqCopyManagerReadyEventHandlerConstruct(
    //   this,
    //   'bssh_fastq_copy_ready_event_submitter',
    //   {
    //     eventBusObj: props.eventBusObj,
    //     tableObj: props.workflowManagerTableObj,
    //   }
    // );
  }
}
