/*

Construct the stacky glue for generating a cttso v2 glue stack

Connect the cttso v2 outputs to pieriandx

*/

import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PieriandxInitialiseLibraryConstruct } from './part_1/initialise-library-db';
import { Cttsov2CompleteToPieriandxConstruct } from './part_2/cttso-v2-output-to-pieriandx-ready-event';
import { NestedStack } from 'aws-cdk-lib/core';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface pieriandxGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  pieriandxGlueTableObj: dynamodb.ITableV2;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
  /* Extras */
  pieriandxProjectInfoSsmParameterObj: ssm.IStringParameter;
  redcapLambdaObj: lambda.IFunction;
}

export class PieriandxGlueHandlerConstruct extends NestedStack {
  constructor(scope: Construct, id: string, props: pieriandxGlueHandlerConstructProps) {
    super(scope, id);
    /*
    Part 1

    Input Event Source: `orcabus.instrumentrunmanager`
    Input Event DetailType: `SamplesheetMetadataUnion`
    Input Event status: `LibraryInSamplesheet`

    * Initialise pieriandx instrument db construct
    */
    const PieriandxInitialiseLibrary = new PieriandxInitialiseLibraryConstruct(
      this,
      'pieriandx_initialise_library',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.pieriandxGlueTableObj,
      }
    );

    /*
    Part 2

    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `succeeded`

    Output Event source: `orcabus.pieriandxinputeventglue`
    Output Event DetailType: `WorkflowDraftRunStateChange`
    Output Event status: `draft`

    * Populate the fastq list row attributes for the rgid for this workflow
    */

    const cttsov2CompleteToPieriandxReady = new Cttsov2CompleteToPieriandxConstruct(
      this,
      'cttsov2_to_pieriandx',
      {
        /* Events*/
        eventBusObj: props.eventBusObj,

        /* Tables */
        tableObj: props.pieriandxGlueTableObj,

        /* Secrets Manager */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Extras */
        projectInfoSsmParameterObj: props.pieriandxProjectInfoSsmParameterObj,
        redcapLambdaObj: props.redcapLambdaObj,
      }
    );
  }
}
