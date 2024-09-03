import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { RnasumInitialiseSubjectDbRowConstruct } from './part_1/initialise-rnasum-subject-dbs';
import { UmccriseAndWtsCompleteToRnasumDraftDraftConstruct } from './part_2/umccrise-and-wts-complete-to-rnasum-draft';
import { RnasumInputMakerConstruct } from './part_3/rnasum-draft-to-ready';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface umccriseGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  rnasumGlueTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class RnasumGlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: umccriseGlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `SubjectInSamplesheet`

    * Initialise rnasum instrument db construct
    */
    const rnasum_initialise_subject = new RnasumInitialiseSubjectDbRowConstruct(
      this,
      'rnasum_initialise_subject',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.rnasumGlueTableObj,
      }
    );

    /*
    Part 2

    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `succeeded`

    Output Event source: `orcabus.umccriseinputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`

    * Populate the fastq list row attributes for the rgid for this workflow
    */

    const umccrise_and_wts_to_rnasum_draft = new UmccriseAndWtsCompleteToRnasumDraftDraftConstruct(
      this,
      'umccrise_and_wts_to_rnasum_draft',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.rnasumGlueTableObj,
        workflowsTableObj: props.inputMakerTableObj,
      }
    );

    /*
    Part 3

    Input Event source: `orcabus.rnasuminputeventglue`
    Input Event DetailType: `WorkflowDraftRunStateChange`
    Input Event status: `draft`

    Output Event source: `orcabus.rnasuminputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `ready`

    * The rnasumInputMaker, subscribes to the rnasum input event glue (itself) and generates a ready event for the rnasumReadySfn
      * However, in order to be 'READY' we need to use a few more variables such as
        * icaLogsUri,
        * analysisOutputUri
        * cacheUri
        * projectId
        * userReference
    */
    const rnasumInputMaker = new RnasumInputMakerConstruct(this, 'rnasum_input_maker_construct', {
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
