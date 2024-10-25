import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { Cttsov2InitialiseLibraryAndFastqListRowConstruct } from './part_1/initialise-cttsov2-library-dbs';
import { Cttsov2PopulateFastqListRowConstruct } from './part_2/populate-fastq-list-row-dbs';
import { Cttsov2FastqListRowShowerCompleteToWorkflowDraftConstruct } from './part_3/fastq-list-row-event-shower-complete-to-cttsov2-ready';
import { NestedStack } from 'aws-cdk-lib/core';

/*
Provide the glue to get from the bssh fastq copy manager to submitting cttsov2 analyses
*/

export interface cttsov2GlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  cttsov2GlueTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class Cttsov2GlueHandlerConstruct extends NestedStack {
  constructor(scope: Construct, id: string, props: cttsov2GlueHandlerConstructProps) {
    super(scope, id);

    /*
        Part 1

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
        Part 2

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
        Part 3

        Input Event Source: `orcabus.instrumentrunmanager`
        Input Event DetailType: `FastqListRowStateChange`
        Input Event status: `FastqListRowEventShowerComplete`

        Output Event source: `orcabus.cttsov2inputeventglue`
        Output Event DetailType: `WorkflowDraftRunStateChange`
        Output Event status: `draft`

        * Trigger cttsov2 events collecting all cttsov2 in the run

        */
    const fastq_list_row_shower_complete_to_workflow_ready =
      new Cttsov2FastqListRowShowerCompleteToWorkflowDraftConstruct(
        this,
        'fastq_list_row_shower_complete_to_workflow_draft',
        {
          /* Events */
          eventBusObj: props.eventBusObj,
          /* Tables */
          cttsov2GlueTableObj: props.cttsov2GlueTableObj,
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
