import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BSSHFastqCopyManagerEventRelayer } from './constructs/part_1/bssh-fastq-copy-manager-event-relayer';
import { updateDataBaseOnNewFastqListRowsEventConstruct } from './constructs/part_2/update-database-on-new-fastq-list-rows';
import { BclconvertInteropqcInputMakerConstruct } from './constructs/part_3/bclconvert-interopqc-input-maker';
import { BclconvertInteropqcManagerReadyEventHandlerConstruct } from './constructs/part_4/bclconvert-interopqc-ready-event-submitter';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface BclconvertManagerEventHandlerConstructProps {
  eventBusObj: events.IEventBus;
  workflowManagerTableObj: dynamodb.ITableV2;
  instrumentRunTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  bclconvertInteropQcUriPrefixSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class BsshFastqCopyEventHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: BclconvertManagerEventHandlerConstructProps) {
    super(scope, id);

    /*
        Part 1
        Input Event Source: `orcabus.bsshfastqcopymanager`
        Input Event DetailType: `WorkflowRunStateChange`
        Input Event status: `succeeded`

        Output Event source: `orcabus.workflowmanager`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `complete`

        * The BSSHFastqCopyManagerEventHandler Construct
          * This will be triggered by the completion event from the BSSHFastqCopyManager Construct.
          * Contains a standard workflow run statechange, the fastqlistrowgzipped, and instrument run id
          * Pushes a workflow run manager event saying that the BSSHFastqCopyManager has complete.
        */
    // const bsshfastqCopyManagerEventRelayerSuccessEventRelayer =
    //   new BSSHFastqCopyManagerEventRelayer(
    //     this,
    //     'bssh_fastq_copy_manager_event_relayer_success_event_relayer',
    //     {
    //       eventBusObj: props.eventBusObj,
    //       tableObj: props.workflowManagerTableObj,
    //     }
    //   );

    /*
        Part 2
        Input Event Source: `orcabus.workflowmanager`
        Input Event DetailType: `WorkflowRunStateChange`
        Input Event status: `complete`

        Output Event source: `orcabus.instrumentrunmanager`
        Output Event DetailType: `orcabus.librarystatechange`
        Output Event status: `fastqlistrowsregistered`

        * The UpdateDataBaseOnNewFastqListRows Construct
          * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and updates the database:
            * Registers all fastq list rows in the database and tie them to the libraryrunid
            * Appends libraryrunids to the library ids in the samplesheet
            * Pushes an event to say that some fastq list rows have been added to the database, with a list of affected library ids and the instrument run id

        */
    const updateDataBaseOnNewFastqListRows = new updateDataBaseOnNewFastqListRowsEventConstruct(
      this,
      'update_database_on_new_fastq_list_rows',
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

        Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `complete`

        * The BCLConvertInteropQCInputMaker Construct
          * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
          * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter
        */
    const bclconvertInteropqcInputMaker = new BclconvertInteropqcInputMakerConstruct(
      this,
      'bclconvert_interopqc_input_maker',
      {
        eventBusObj: props.eventBusObj,
        outputUriPrefixSsmParameterObj: props.bclconvertInteropQcUriPrefixSsmParameterObj,
        tableObj: props.inputMakerTableObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      }
    );

    /*
        Part 4

        Input Event Source: `orcabus.bclconvertinteropqcinputeventglue`
        Input Event DetailType: `WorkflowRunStateChange`
        Input Event status: `complete`

        Output Event source: `orcabus.workflowmanager`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `ready`

        * The BCLConvertInteropQCReadyEventSubmitter Construct
          * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and generates a ready event for the BCLConvertInteropQC

        */
    // const bclconvertInteropqcManagerReadyEvent =
    //   new BclconvertInteropqcManagerReadyEventHandlerConstruct(
    //     this,
    //     'bclconvert_interopqc_ready_event_submitter',
    //     {
    //       eventBusObj: props.eventBusObj,
    //       tableObj: props.workflowManagerTableObj,
    //     }
    //   );
  }
}
