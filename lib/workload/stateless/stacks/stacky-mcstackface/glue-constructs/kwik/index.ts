import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { WgtsQcInitialiseInstrumentRunDbRowConstruct } from './part_1/initialise-wgts-instrument-run-db';
import { WgtsQcInitialiseLibraryAndFastqListRowConstruct } from './part_2/initialise-wgts-library-dbs';
import { WgtsQcPopulateFastqListRowConstruct } from './part_3/populate-fastq-list-row-dbs';
import { WgtsQcFastqListRowShowerCompleteToWorkflowDraftConstruct } from './part_4/fastq-list-rows-shower-complete-to-wgts-qc-draft';
import { WgtsQcInputMakerConstruct } from './part_5/wgts-qc-draft-to-ready';
import { FastqListRowQcCompleteConstruct } from './part_6/push-fastq-list-row-qc-complete-event';
import { WgtsQcLibraryQcCompleteConstruct } from './part_7/library-qc-complete-event';

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
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
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
        /* Event bus */
        eventBusObj: props.eventBusObj,
        /* Tables */
        inputMakerTableObj: props.inputMakerTableObj,
        /* SSM Param objects */
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
      }
    );

    /*
    Part 6

    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `succeeded`
    Input Event WorkflowName: `wgts_qc`

    Output Event Source: `orcabus.wgtsqcinputeventglue`
    Output Event DetailType: `FastqListRowStateChange`
    Output Event status: `QcComplete`

    * Subscribe to workflow run state change events, map the fastq list row id from the portal run id in the data base
    * We output the fastq list row id to the event bus with the status `QcComplete`
    */
    const wgtsQcCompleteToFastqListRowQcComplete = new FastqListRowQcCompleteConstruct(
      this,
      'fastq_list_row_qc_complete',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.wgtsQcGlueTableObj,
        icav2JwtSecretsObj: props.icav2AccessTokenSecretObj,
      }
    );

    /*
    Part 7

    Input Event Source: `orcabus.wgtsqcinputeventglue`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `QcComplete`

    Output Event Source: `orcabus.wgtsqcinputeventglue`
    Output Event DetailType: `LibraryStateChange`
    Output Event status: `QcComplete`

    * Once all fastq list rows have been processed for a given library, we fire off a library state change event
    * This will contain the qc information such as coverage + duplicate rate (for wgs) or exon coverage (for wts)
    */
    const FastqListRowQcCompleteToLibraryQcComplete = new WgtsQcLibraryQcCompleteConstruct(
      this,
      'wgts_qc_complete_to_fastq_list_row_qc_complete',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.wgtsQcGlueTableObj,
      }
    );
  }
}
