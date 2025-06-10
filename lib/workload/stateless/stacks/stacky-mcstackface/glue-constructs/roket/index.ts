import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { UmccriseAndWtsCompleteToRnasumReadyConstruct } from './part_2/umccrise-and-wts-complete-to-rnasum-draft';
import { TnInitialiseLibraryAndFastqListRowConstruct } from '../loctite/part_1/initialise-tn-library-dbs';
import { RnasumInitialiseLibraryConstruct } from './part_1/initialise-rnasum-library-dbs';
import { NestedStack } from 'aws-cdk-lib/core';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface umccriseGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  rnasumGlueTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class RnasumGlueHandlerConstruct extends NestedStack {
  constructor(scope: Construct, id: string, props: umccriseGlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1
    Input Event Source: `orcabus.fastqglue`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `LibraryInSamplesheet`

    * Initialise rnasum library and fastq list row constructs
    */

    const rnasumInitialiseLibraryAndFastqListRow = new RnasumInitialiseLibraryConstruct(
      this,
      'rnasum_initialise_library_and_fastq_list_row',
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
    Output Event status: `ready`

    * Populate the fastq list row attributes for the rgid for this workflow
    */
    const umccriseAndWtsToRnasumDraft = new UmccriseAndWtsCompleteToRnasumReadyConstruct(
      this,
      'umccrise_and_wts_to_rnasum_draft',
      {
        /* Events */
        eventBusObj: props.eventBusObj,

        /* Tables */
        tableObj: props.rnasumGlueTableObj,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
      }
    );
  }
}
