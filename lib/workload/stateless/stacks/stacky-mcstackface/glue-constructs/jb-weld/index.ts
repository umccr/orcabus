import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Cttsov2InitialiseInstrumentRunDbRowConstruct } from './part_1/initialise-cttsov2-instrument-dbs';
import { Cttsov2InitialiseLibraryAndFastqListRowConstruct } from './part_2/initialise-cttsov2-library-dbs';
import { Cttsov2PopulateFastqListRowConstruct } from './part_3/populate-fastq-list-row-dbs';
import { Cttsov2FastqListRowShowerCompleteToWorkflowDraftConstruct } from './part_4/fastq-list-row-event-shower-complete-to-cttsov2-draft';
import { Cttsov2InputMakerConstruct } from './part_5/cttsov2-draft-to-ready';

/*
Provide the glue to get from the bssh fastq copy manager to submitting cttsov2 analyses
*/

export interface cttsov2GlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  cttsov2GlueTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class Cttsov2GlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: cttsov2GlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1
    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetShowerStateChange`
    Input Event status: `SamplesheetRegisteredEventShowerStarting`

    * Initialise cttsov2 instrument db construct
    */
    const cttsov2_initialise_instrument_run_db_row =
      new Cttsov2InitialiseInstrumentRunDbRowConstruct(
        this,
        'initialise_cttsov2_instrument_run_db_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.cttsov2GlueTableObj,
        }
      );

    /*
    Part 2

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `LibraryInSamplesheet`

    * Initialise cttsov2 instrument db construct
    */
    const cttsov2_initialise_library_and_fastq_list_row =
      new Cttsov2InitialiseLibraryAndFastqListRowConstruct(
        this,
        'initialise_cttsov2_library_and_fastq_list_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.cttsov2GlueTableObj,
        }
      );

    /*
    Part 3

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `newFastqListRow`

    * Populate the fastq list row attributes for the rgid for this workflow
    */
    const cttsov2_populate_fastq_list_row = new Cttsov2PopulateFastqListRowConstruct(
      this,
      'populate_cttsov2_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.cttsov2GlueTableObj,
      }
    );

    /*
    Part 4

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `FastqListRowEventShowerComplete`

    Output Event source: `orcabus.cttsov2inputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`

    * Trigger cttsov2 events collecting all cttsov2 in the run

    */
    const fastq_list_row_shower_complete_to_workflow_draft =
      new Cttsov2FastqListRowShowerCompleteToWorkflowDraftConstruct(
        this,
        'fastq_list_row_shower_complete_to_workflow_draft',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.cttsov2GlueTableObj,
        }
      );

    /*
    Part 5
    Input Event source: `orcabus.cttsov2inputeventglue`
    Input Event DetailType: `WorkflowDraftRunStateChange`
    Input Event status: `draft`

    Output Event source: `orcabus.cttsov2inputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `ready`
    */
    const fastqListRowsToctTSOv2InputMaker = new Cttsov2InputMakerConstruct(
      this,
      'fastq_list_rows_to_cttso_v2_input_maker',
      {
        // Event bus
        eventBusObj: props.eventBusObj,
        // SSM Param objects
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
        // Tables
        inputMakerTableObj: props.inputMakerTableObj,
      }
    );
  }
}
