import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as cdk from 'aws-cdk-lib';
import { showerGlueHandlerConstruct } from './clag';
import { BclconvertToBsshFastqCopyEventHandlerConstruct } from './elmer';
import { BsshFastqCopyToBclconvertInteropQcConstruct } from './gorilla';
import { Cttsov2GlueHandlerConstruct } from './jb-weld';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface GlueConstructProps {
  /* Event Bus */
  eventBusObj: events.IEventBus;
  /* Tables */
  instrumentRunTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  workflowManagerTableObj: dynamodb.ITableV2;
  cttsov2GlueTableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  bsshOutputFastqCopyOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
}

export class GlueConstruct extends Construct {
  constructor(scope: Construct, id: string, props: GlueConstructProps) {
    super(scope, id);

    /*
        Part A: Send 'showered' events if a new samplesheet arrives or new fastq list rows arrive
        */
    const clag = new showerGlueHandlerConstruct(this, 'clag', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      instrumentRunTableObj: props.instrumentRunTableObj,
    });

    /*
    Part B: Copy the fastq list rows by connecting the bclconvert manager completion with the bsshfastqcopy manager
    */
    const elmer = new BclconvertToBsshFastqCopyEventHandlerConstruct(this, 'elmer', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      inputMakerTableObj: props.inputMakerTableObj,
      /* SSM Parameters */
      bsshOutputFastqCopyUriSsmParameterObj: props.bsshOutputFastqCopyOutputUriSsmParameterObj,
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
    });

    /*
        Part C: Connect the bclconvert interop qc
        */
    const gorilla = new BsshFastqCopyToBclconvertInteropQcConstruct(this, 'gorilla', {
      /* Event Objects */
      eventBusObj: props.eventBusObj,
      /* Table Objects */
      inputMakerTableObj: props.inputMakerTableObj,
      /* SSM Parameter Ojbects */
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
    });

    /*
        Part D: Plumber-up the cttso v2 to the shower services
        */
    const jb_weld = new Cttsov2GlueHandlerConstruct(this, 'jb_weld', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      inputMakerTableObj: props.inputMakerTableObj,
      cttsov2GlueTableObj: props.cttsov2GlueTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
    });

    /*
        Part E: Plumber-up the WGTS QC Execution Service to the shower services
        */
    // TODO

    /*
        Part F: Plumber-up the Tumor-Normal Execution Service to the shower services
        */
    // TODO
  }
}

export interface GlueStackConfig {
  /* Event Bus */
  eventBusName: string;
  /* Tables */
  instrumentRunTableName: string;
  inputMakerTableName: string;
  workflowManagerTableName: string;
  cttsov2GlueTableName: string;
  /* SSM Parameters */
  icav2ProjectIdSsmParameterName: string;
  bsshOutputFastqCopyUriSsmParameterName: string;
  analysisCacheUriSsmParameterName: string;
  analysisOutputUriSsmParameterName: string;
  analysisLogsUriSsmParameterName: string;
}

export type GlueStackProps = GlueStackConfig & cdk.StackProps;

export class GlueStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: GlueStackProps) {
    super(scope, id, props);

    /*
        Part 0: Get the inputs as objects
        */

    /*
        Get the event bus
        */
    const eventBusObj = events.EventBus.fromEventBusName(this, 'eventBusObj', props.eventBusName);

    /*
        Get the tables
        */
    const workflowManagerTableObj = dynamodb.Table.fromTableName(
      this,
      'workflowManagerTableObj',
      props.workflowManagerTableName
    );
    const inputMakerTableObj = dynamodb.Table.fromTableName(
      this,
      'inputMakerTableObj',
      props.inputMakerTableName
    );
    const instrumentRunTableObj = dynamodb.Table.fromTableName(
      this,
      'instrumentRunTableObj',
      props.instrumentRunTableName
    );
    const cttsov2GlueTableObj = dynamodb.Table.fromTableName(
      this,
      'cttsov2GlueTableObj',
      props.cttsov2GlueTableName
    );

    /*
        Get the SSM Parameters
        */
    const icav2ProjectIdSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'icav2ProjectIdSsmParameterObj',
      props.icav2ProjectIdSsmParameterName
    );
    const bsshOutputFastqCopyUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'bsshOutputFastqCopyUriPrefixSsmParameterObj',
      props.bsshOutputFastqCopyUriSsmParameterName
    );

    const analysisCacheUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'analysisCacheUriPrefixSsmParameterObj',
      props.analysisCacheUriSsmParameterName
    );
    const analysisOutputUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'analysisOutputUriPrefixSsmParameterObj',
      props.analysisOutputUriSsmParameterName
    );

    const analysisLogsUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'analysisLogsUriPrefixSsmParameterObj',
      props.analysisLogsUriSsmParameterName
    );

    /*
        Call the construct
        */
    new GlueConstruct(this, 'stacky_glue', {
      eventBusObj: eventBusObj,
      cttsov2GlueTableObj: cttsov2GlueTableObj,
      workflowManagerTableObj: workflowManagerTableObj,
      inputMakerTableObj: inputMakerTableObj,
      instrumentRunTableObj: instrumentRunTableObj,
      icav2ProjectIdSsmParameterObj: icav2ProjectIdSsmParameterObj,
      bsshOutputFastqCopyOutputUriSsmParameterObj: bsshOutputFastqCopyUriSsmParameterObj,
      analysisOutputUriSsmParameterObj: analysisOutputUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: analysisCacheUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: analysisLogsUriSsmParameterObj,
    });
  }
}
