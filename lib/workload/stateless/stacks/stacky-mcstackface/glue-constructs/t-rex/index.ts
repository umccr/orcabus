/*
Capture wgs libraries

Track oncoanalyser-wgts-dna succeeded events with matches to wts and wgs libraries

Launch oncoanalyser-both for subjects with wts and wgs libraries

Launch sash for wgs libraries
*/

import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import { OncoanalyserBothInitialiseLibraryAndFastqListRowConstruct } from './part_1/initialise-wts-wgs-libraries';
import { OncoanalyserDnaToSashReadyConstruct } from './part_2/oncoanalyser-dna-complete-to-sash-ready';
import { OncoanalyserDnaRnaReadyConstruct } from './part_3/oncoanalyser-dna-or-rna-to-oncoanalyser-both-ready';
import { NestedStack } from 'aws-cdk-lib/core';

export interface OncoanalyserBothSashGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  oncoanalyserBothSashGlueTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
}

export class OncoanalyserBothSashGlueHandlerConstruct extends NestedStack {
  constructor(scope: Construct, id: string, props: OncoanalyserBothSashGlueHandlerConstructProps) {
    super(scope, id);

    /*
      Part 1

      Input Event Source: `orcabus.instrumentrunmanager`
      Input Event DetailType: `SamplesheetMetadataUnion`
      Input Event status: `LibraryInSamplesheet`

      * Initialise oncoanalyser instrument db construct
      */
    const oncoanalyser_initialise_library_and_fastq_list_row =
      new OncoanalyserBothInitialiseLibraryAndFastqListRowConstruct(
        this,
        'initialise_oncoanalyser_both_library_and_fastq_list_row',
        {
          eventBusObj: props.eventBusObj,
          tableObj: props.oncoanalyserBothSashGlueTableObj,
        }
      );

    /*
        Part 2

        Input Event Source: `orcabus.workflowmanager`
        Input Event DetailType: `WorkflowRunStateChangeComplete`
        Input Event status: `SUCCEEDED`
        Input Event workflow type: oncoanalyser-wgts-dna

        Output Event source: `orcabus.oncoanalyserinputeventglue`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `READY`

        * Trigger oncoanalyser-both events collecting all oncoanalyser in the run

      */
    const oncoanalyser_dna_rna_sash_ready = new OncoanalyserDnaToSashReadyConstruct(
      this,
      'fastq_list_row_shower_complete_to_workflow_draft',
      {
        /* Events */
        eventBusObj: props.eventBusObj,
        /* Tables */
        tableObj: props.oncoanalyserBothSashGlueTableObj,
        /* SSM Param objects */
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      }
    );

    /*
        Part 3

        Input Event Source: `orcabus.workflowmanager`
        Input Event DetailType: `WorkflowRunStateChangeComplete`
        Input Event status: `SUCCEEDED`
        Input Event workflow type: oncoanalyser-wgts-dna /

        Output Event source: `orcabus.oncoanalyserinputeventglue`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `READY`

        * Trigger oncoanalyser-both events collecting all oncoanalyser in the run

      */

    const oncoanalyser_dna_rna_both = new OncoanalyserDnaRnaReadyConstruct(
      this,
      'oncoanalyser_dna_rna_both',
      {
        /* Events */
        eventBusObj: props.eventBusObj,
        /* Tables */
        tableObj: props.oncoanalyserBothSashGlueTableObj,
        /* SSM Param objects */
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      }
    );
  }
}
