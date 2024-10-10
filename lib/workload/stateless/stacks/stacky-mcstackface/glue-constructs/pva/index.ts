import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { UmccriseInitialiseLibraryConstruct } from './part_1/initialise-umccrise-library-dbs';
import { TnCompleteToUmccriseReadyConstruct } from './part_2/tn-complete-to-umccrise-draft';

/*
Provide the glue to get from the bssh fastq copy manager to submitting wgts qc analyses
*/

export interface umccriseGlueHandlerConstructProps {
  /* General */
  eventBusObj: events.IEventBus;
  /* Tables */
  umccriseGlueTableObj: dynamodb.ITableV2;
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
    Input Event status: `LibraryInSamplesheet`

    * Initialise umccrise instrument db construct
    */
    const UmccriseInitialiseLibrary = new UmccriseInitialiseLibraryConstruct(
      this,
      'umccrise_initialise_library',
      {
        eventBusObj: props.eventBusObj,
        tableObj: props.umccriseGlueTableObj,
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

    const tnCompleteToUmccriseReady = new TnCompleteToUmccriseReadyConstruct(
      this,
      'tn_to_umccrise',
      {
        /* Events*/
        eventBusObj: props.eventBusObj,
        /* Tables */
        tableObj: props.umccriseGlueTableObj,
        /* SSM Param objects */
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        outputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        cacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
        logsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
        /* Secrets Manager */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
      }
    );
  }
}
