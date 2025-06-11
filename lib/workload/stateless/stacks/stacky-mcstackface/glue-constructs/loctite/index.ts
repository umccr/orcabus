import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { TnInitialiseLibraryAndFastqListRowConstruct } from './part_1/initialise-tn-library-dbs';
import { TnPopulateFastqListRowConstruct } from './part_2/update-fastq-list-rows-dbs';
import { LibraryQcCompleteToTnReadyConstruct } from './part_3/library-qc-complete-db-to-tn-ready';
import { NestedStack } from 'aws-cdk-lib/core';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface tnGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  tnGlueTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class TnGlueHandlerConstruct extends NestedStack {
  constructor(scope: Construct, id: string, props: tnGlueHandlerConstructProps) {
    super(scope, id);

    /*
        Part 1

        Input Event Source: `orcabus.fastqglue`
        Input Event DetailType: `SamplesheetMetadataUnion`
        Input Event status: `LibraryInSamplesheet`

        * Initialise wgts qc library and fastq list row constructs
        */
    const tnInitialiseLibraryAndFastqListRow = new TnInitialiseLibraryAndFastqListRowConstruct(
      this,
      'tn_initialise_library_and_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.tnGlueTableObj,
      }
    );

    /*
        Part 2

        Input Event Source: `orcabus.fastqglue`
        Input Event DetailType: `StackyFastqListRowStateChange`
        Input Event status: `newFastqListRow`

        * Populate the fastq list row attributes for the rgid for this workflow
        */
    const tnPopulateFastqListRow = new TnPopulateFastqListRowConstruct(
      this,
      'tn_populate_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.tnGlueTableObj,
      }
    );

    /*
        Part 3
        Input Event source: `orcabus.wgtsqcinputeventglue`
        Input Event DetailType: `LibraryStateChange`
        Input Event status: `QcComplete`

        Output Event source: `orcabus.tninputeventglue`
        Output Event DetailType: `WorkflowDraftRunStateChange`
        Output Event status: `draft`
        */
    const libraryQcCompleteToTnDraft = new LibraryQcCompleteToTnReadyConstruct(
      this,
      'library_qc_complete_to_tn_draft',
      {
        // Event bus
        eventBusObj: props.eventBusObj,
        // Table objects
        tableObj: props.tnGlueTableObj,
        /* SSM Param objects */
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
      }
    );
  }
}
