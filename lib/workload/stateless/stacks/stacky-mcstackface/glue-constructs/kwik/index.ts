import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { WgtsQcInitialiseInstrumentRunDbRowConstruct } from './part_1/initialise-wgts-instrument-run-db';
import { WgtsQcInitialiseLibraryAndFastqListRowConstruct } from './part_2/initialise-wgts-library-dbs';
import { WgtsQcPopulateFastqListRowConstruct } from './part_3/populate-fastq-list-row-dbs';
import { WgtsQcFastqListRowShowerCompleteToWorkflowDraftConstruct } from './part_4/fastq-list-rows-shower-complete-to-wgts-qc-draft';
import { WgtsQcInputMakerConstruct } from './part_5/wgts-qc-draft-to-ready';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface wgtsQcGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  wgtsQcGlueTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class WgtsQcGlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: wgtsQcGlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1
    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetShowerStateChange`
    Input Event status: `SamplesheetRegisteredEventShowerStarting`

    * Initialise wgts qc instrument db construct
    */
    const wgts_qc_initialise_instrument_run_db_row =
      new WgtsQcInitialiseInstrumentRunDbRowConstruct(
        this,
        'initialise_wgts_qc_instrument_run_db_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.wgtsQcGlueTableObj,
        }
      );

    /*
    Part 2

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `LibraryInSamplesheet`

    * Initialise wgts qc library and fastq list row constructs
    */
    const wgts_qc_initialise_library_and_fastq_list_row =
      new WgtsQcInitialiseLibraryAndFastqListRowConstruct(
        this,
        'initialise_wgts_qc_library_and_fastq_list_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.wgtsQcGlueTableObj,
        }
      );

    /*
    Part 3

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `newFastqListRow`

    * Populate the fastq list row attributes for the rgid for this workflow
    */
    const wgts_qc_populate_fastq_list_row = new WgtsQcPopulateFastqListRowConstruct(
      this,
      'wgts_qc_populate_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.wgtsQcGlueTableObj,
      }
    );

    /*
    Part 4

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `FastqListRowEventShowerComplete`

    Output Event source: `orcabus.wgtsqcinputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`

    * Trigger wgts qc events collecting all wgts qc libraries in the run

    */
    const fastq_list_row_shower_complete_to_workflow_draft =
      new WgtsQcFastqListRowShowerCompleteToWorkflowDraftConstruct(
        this,
        'fastq_list_row_shower_complete_to_workflow_draft',
        {
          workflowsTableObj: props.inputMakerTableObj,
          eventBusObj: props.eventBusObj,
          wgtsQcGlueTableObj: props.wgtsQcGlueTableObj,
        }
      );

    /*
    Part 5
    Input Event source: `orcabus.wgtsqcinputeventglue`
    Input Event DetailType: `WorkflowDraftRunStateChange`
    Input Event status: `draft`

    Output Event source: `orcabus.wgtsqcinputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `ready`
    */
    const fastqListRowsToWgtsQcInputMaker = new WgtsQcInputMakerConstruct(
      this,
      'fastq_list_rows_to_wgts_qc_input_maker',
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
