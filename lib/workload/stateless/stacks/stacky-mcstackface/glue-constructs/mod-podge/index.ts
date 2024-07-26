import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { WtsInitialiseLibraryAndFastqListRowConstruct } from './part_1/initialise-wts-library-dbs';
import { WtsPopulateFastqListRowConstruct } from './part_2/update-fastq-list-rows-dbs';
import { WtsFastqListRowQcCompleteConstruct } from './part_3/update-fastq-list-row-qc-complete-dbs';
import { LibraryQcCompleteToWtsDraftConstruct } from './part_4/library-qc-complete-to-wts-draft';
import { WtsInputMakerConstruct } from './part_5/wts-draft-to-ready';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface wtsGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  wtsGlueTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class WtsGlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: wtsGlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `LibraryInSamplesheet`

    * Initialise wts instrument db construct
    */
    const wts_initialise_library_and_fastq_list_row =
      new WtsInitialiseLibraryAndFastqListRowConstruct(
        this,
        'wts_initialise_library_and_fastq_list_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.wtsGlueTableObj,
        }
      );

    /*
    Part 2

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `newFastqListRow`

    * Populate the fastq list row attributes for the rgid for this workflow
    */

    const wts_populate_fastq_list_row = new WtsPopulateFastqListRowConstruct(
      this,
      'wts_populate_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.wtsGlueTableObj,
      }
    );

    /*
    Part 3

    Input Event Source: `orcabus.wgtsqcinputeventglue`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `QcComplete`

    * Populate the fastq list row attributes for the rgid for this workflow
    */

    const wts_fastq_list_row_qc_complete = new WtsFastqListRowQcCompleteConstruct(
      this,
      'wts_fastq_list_row_qc_complete',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.wtsGlueTableObj,
      }
    );

    /*
    Part 4

    Input Event Source: `orcabus.wgtsqcinputeventglue`
    Input Event DetailType: `LibraryStateChange`
    Input Event status: `QcComplete`

    Output Event Source: `orcabus.wtsinputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`

    * Subscribe to the wgts input event glue, library complete event.
    * Launch a draft event for the wts pipeline if the libraries' subject has a complement library that is also complete
    */
    const libraryQcCompleteToWtsDraft = new LibraryQcCompleteToWtsDraftConstruct(
      this,
      'library_qc_complete_to_wts_draft',
      {
        // Event bus
        eventBusObj: props.eventBusObj,
        // SSM Param objects
        tableObj: props.wtsGlueTableObj,
        workflowsTableObj: props.inputMakerTableObj,
      }
    );

    /*
    Part 5

    Input Event source: `orcabus.wtsinputeventglue`
    Input Event DetailType: `WorkflowDraftRunStateChange`
    Input Event status: `draft`

    Output Event source: `orcabus.wtsinputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `ready`

    * The wtsInputMaker, subscribes to the wts input event glue (itself) and generates a ready event for the wtsReadySfn
      * However, in order to be 'ready' we need to use a few more variables such as
        * icaLogsUri,
        * analysisOutputUri
        * cacheUri
        * projectId
        * userReference
    */
    const wtsInputMaker = new WtsInputMakerConstruct(this, 'fastq_list_row_qc_complete', {
      // Event bus
      eventBusObj: props.eventBusObj,
      // SSM Param objects
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      // Tables
      inputMakerTableObj: props.inputMakerTableObj,
    });
  }
}
