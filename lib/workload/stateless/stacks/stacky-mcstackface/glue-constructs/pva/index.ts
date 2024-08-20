import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { UmccriseInitialiseSubjectDbRowConstruct } from './part_1/initialise-umccrise-subject-dbs';
import { UmccriseInitialiseLibraryAndFastqListRowConstruct } from './part_2/initialise-umccrise-library-dbs';
import { UmccrisePopulateFastqListRowConstruct } from './part_3/update-fastq-list-rows-dbs';
import { TnCompleteToUmccriseDraftConstruct } from './part_4/tn-complete-to-umccrise-draft';
import { UmccriseInputMakerConstruct } from './part_5/umccrise-draft-to-ready';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface umccriseGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  umccriseGlueTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class UmccriseGlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: umccriseGlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `SubjectInSamplesheet`

    * Initialise umccrise instrument db construct
    */
    const umccrise_initialise_subject = new UmccriseInitialiseSubjectDbRowConstruct(
      this,
      'umccrise_initialise_subject',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.umccriseGlueTableObj,
      }
    );

    /*
    Part 2

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `LibraryInSamplesheet`

    * Initialise umccrise instrument db construct
    */
    const umccrise_initialise_library_and_fastq_list_row =
      new UmccriseInitialiseLibraryAndFastqListRowConstruct(
        this,
        'umccrise_initialise_library_and_fastq_list_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.umccriseGlueTableObj,
        }
      );

    /*
    Part 3

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `FastqListRowStateChange`
    Input Event status: `newFastqListRow`

    * Populate the fastq list row attributes for the rgid for this workflow
    */

    const umccrise_populate_fastq_list_row = new UmccrisePopulateFastqListRowConstruct(
      this,
      'umccrise_populate_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.umccriseGlueTableObj,
      }
    );

    /*
    Part 4

    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `succeeded`

    Output Event source: `orcabus.umccriseinputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`

    * Populate the fastq list row attributes for the rgid for this workflow
    */

    const tn_to_umccrise_draft = new TnCompleteToUmccriseDraftConstruct(
      this,
      'tn_to_umccrise_draft',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.umccriseGlueTableObj,
        workflowsTableObj: props.inputMakerTableObj,
      }
    );

    /*
    Part 5

    Input Event source: `orcabus.umccriseinputeventglue`
    Input Event DetailType: `WorkflowDraftRunStateChange`
    Input Event status: `draft`

    Output Event source: `orcabus.umccriseinputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `ready`

    * The umccriseInputMaker, subscribes to the umccrise input event glue (itself) and generates a ready event for the umccriseReadySfn
      * However, in order to be 'ready' we need to use a few more variables such as
        * icaLogsUri,
        * analysisOutputUri
        * cacheUri
        * projectId
        * userReference
    */
    const umccriseInputMaker = new UmccriseInputMakerConstruct(this, 'fastq_list_row_qc_complete', {
      /* Event bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      inputMakerTableObj: props.inputMakerTableObj,
      /* SSM Param objects */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      /* Secrets Manager */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    });
  }
}
