import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { TnInitialiseSubjectDbRowConstruct } from './part_1/initialise-tn-subject-dbs';
import { TnInitialiseLibraryAndFastqListRowConstruct } from './part_2/initialise-tn-library-dbs';
import { TnPopulateFastqListRowConstruct } from './part_3/update-fastq-list-rows-dbs';
import { TnFastqListRowQcCompleteConstruct } from './part_4/update-fastq-list-row-qc-complete-dbs';
import { LibraryQcCompleteToTnDraftConstruct } from './part_5/library-qc-complete-db-to-tn-draft';
import { TnInputMakerConstruct } from './part_6/tn-draft-to-ready';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface tnGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  tnGlueTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class TnGlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: tnGlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1
    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `SubjectInSamplesheet`

    * Initialise tn subject db row construct
    */
    const tn_initialise_subject_db_row = new TnInitialiseSubjectDbRowConstruct(
      this,
      'tn_initialise_subject_db_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.tnGlueTableObj,
      }
    );

    /*
    Part 2

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `LibraryInSamplesheet`

    * Initialise wgts qc library and fastq list row constructs
    */
    const tn_initialise_library_and_fastq_list_row =
      new TnInitialiseLibraryAndFastqListRowConstruct(
        this,
        'tn_initialise_library_and_fastq_list_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.tnGlueTableObj,
        }
      );

    /*
    Part 3

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `newFastqListRow`

    * Populate the fastq list row attributes for the rgid for this workflow
    */
    const tn_populate_fastq_list_row = new TnPopulateFastqListRowConstruct(
      this,
      'tn_populate_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.tnGlueTableObj,
      }
    );

    /*
    Part 4

    Input Event Source: `orcabus.wgtsqcinputeventglue`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `QcComplete`

    * Populate the fastq list row attributes with the qc metrics for this fastq list row id
    * Currently not used by the glue service

    */
    const tn_fastq_list_row_qc_complete = new TnFastqListRowQcCompleteConstruct(
      this,
      'tn_fastq_list_row_qc_complete',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.tnGlueTableObj,
      }
    );

    /*
    Part 5
    Input Event source: `orcabus.wgtsqcinputeventglue`
    Input Event DetailType: `LibraryStateChange`
    Input Event status: `QcComplete`

    Output Event source: `orcabus.tninputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`
    */
    const libraryQcCompleteToTnDraft = new LibraryQcCompleteToTnDraftConstruct(
      this,
      'library_qc_complete_to_tn_draft',
      {
        // Event bus
        eventBusObj: props.eventBusObj,
        // SSM Param objects
        tableObj: props.tnGlueTableObj,
        workflowsTableObj: props.inputMakerTableObj,
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
    const tnInputMaker = new TnInputMakerConstruct(this, 'fastq_list_row_qc_complete', {
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
    });
  }
}
