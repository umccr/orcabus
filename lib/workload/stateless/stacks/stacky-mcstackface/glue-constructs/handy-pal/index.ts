/*
We initialise the wts libraries and wgs libraries for oncoanalyser

We also initialise the fastq list rows for the wts libraries since
wts workflows will start from fastq
*/

import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import { OncoanalyserInitialiseLibraryAndFastqListRowConstruct } from './part_1/initialise-wts-and-wgs-libraries';
import { OncoanalyserPopulateFastqListRowConstruct } from './part_2/populate-fastq-list-rows';
import { OncoanalyserDnaOrRnaReadyConstruct } from './part_3/launch-oncoanalyser-ready-events';
import { NestedStack } from 'aws-cdk-lib/core';

export interface OncoanalyserGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  oncoanalyserGlueTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
}

export class OncoanalyserGlueHandlerConstruct extends NestedStack {
  constructor(scope: Construct, id: string, props: OncoanalyserGlueHandlerConstructProps) {
    super(scope, id);

    /*
      Part 1

      Input Event Source: `orcabus.fastqglue`
      Input Event DetailType: `SamplesheetMetadataUnion`
      Input Event status: `LibraryInSamplesheet`

      * Initialise oncoanalyser instrument db construct
      */
    const oncoanalyser_initialise_library_and_fastq_list_row =
      new OncoanalyserInitialiseLibraryAndFastqListRowConstruct(
        this,
        'initialise_oncoanalyser_library_and_fastq_list_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.oncoanalyserGlueTableObj,
        }
      );

    /*
        Part 2

        Input Event Source: `orcabus.fastqglue`
        Input Event DetailType: `StackyFastqListRowStateChange`
        Input Event status: `newFastqListRow`

        * Populate the fastq list row attributes for the rgid for this workflow
        */
    const oncoanalyser_populate_fastq_list_row = new OncoanalyserPopulateFastqListRowConstruct(
      this,
      'populate_oncoanalyser_fastq_list_row',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.oncoanalyserGlueTableObj,
      }
    );

    /*
        Part 3

        Input Event Source: `orcabus.fastqglue`
        Input Event DetailType: `StackyFastqListRowStateChange`
        Input Event status: `FastqListRowEventShowerComplete`

        Output Event source: `orcabus.oncoanalyserinputeventglue`
        Output Event DetailType: `WorkflowDraftRunStateChange`
        Output Event status: `draft`

        * Trigger oncoanalyser events collecting all oncoanalyser in the run

        */
    const oncoanalyser_dna_or_rna_ready = new OncoanalyserDnaOrRnaReadyConstruct(
      this,
      'fastq_list_row_shower_complete_to_workflow_draft',
      {
        /* Events */
        eventBusObj: props.eventBusObj,
        /* Tables */
        tableObj: props.oncoanalyserGlueTableObj,
        /* SSM Param objects */
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      }
    );
  }
}
