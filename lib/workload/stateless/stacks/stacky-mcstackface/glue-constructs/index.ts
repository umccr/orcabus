import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BsshFastqCopyEventHandlerConstruct } from './selleys';
import { cttsov2GlueHandlerConstruct } from './super';
import * as cdk from 'aws-cdk-lib';
import {BclconvertManagerEventHandlerConstruct} from "./scotch";

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
  /* SSM Parameters */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  bsshOutputFastqCopyUriPrefixSsmParameterObj: ssm.IStringParameter;
  bclconvertInteropQcUriPrefixSsmParameterObj: ssm.IStringParameter;
  cttsov2OutputUriPrefixSsmParameterObj: ssm.IStringParameter;
  cttsov2CacheUriPrefixSsmParameterObj: ssm.IStringParameter;
}

export class GlueConstruct extends Construct {
  constructor(scope: Construct, id: string, props: GlueConstructProps) {
    super(scope, id);

    /*
    Part A: Glue the bclconvertmanager success event to the bsshFastqCopyManager
    */
    const scotch = new BclconvertManagerEventHandlerConstruct(this, 'scotch', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      workflowManagerTableObj: props.workflowManagerTableObj,
      inputMakerTableObj: props.inputMakerTableObj,
      instrumentRunTableObj: props.instrumentRunTableObj,
      /* SSM Parameters */
      bsshOutputFastqCopyUriPrefixSsmParameterObj: props.bsshOutputFastqCopyUriPrefixSsmParameterObj,
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj
    });

    /*
    Part B: Connect the bsshFastqCopyManager completion to the BCLConvert InterOp QC Manager
    */
    const selleys = new BsshFastqCopyEventHandlerConstruct(this, 'selleys', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      workflowManagerTableObj: props.workflowManagerTableObj,
      inputMakerTableObj: props.inputMakerTableObj,
      instrumentRunTableObj: props.instrumentRunTableObj,
      /* SSM Parameters */
      bclconvertInteropQcUriPrefixSsmParameterObj:
        props.bclconvertInteropQcUriPrefixSsmParameterObj,
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
    });

    /*
    Part C: Connect the BSSH Copy Completion to the cttsov2Manager
    */
    const super_glue = new cttsov2GlueHandlerConstruct(this, 'super', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      workflowManagerTableObj: props.workflowManagerTableObj,
      inputMakerTableObj: props.inputMakerTableObj,
      instrumentRunTableObj: props.instrumentRunTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      cttsov2OutputUriPrefixSsmParameterObj: props.cttsov2OutputUriPrefixSsmParameterObj,
      cttsov2CacheUriPrefixSsmParameterObj: props.cttsov2CacheUriPrefixSsmParameterObj,
    });
  }
}

export interface GlueStackConfig {
  /* Event Bus */
  eventBusName: string;
  /* Tables */
  instrumentRunTableName: string;
  inputMakerTableName: string;
  workflowManagerTableName: string;
  /* SSM Parameters */
  icav2ProjectIdSsmParameterName: string;
  bsshOutputFastqCopyUriPrefixSsmParameterName: string;
  bclconvertInteropQcUriPrefixSsmParameterName: string;
  cttsov2OutputUriPrefixSsmParameterName: string;
  cttsov2CacheUriPrefixSsmParameterName: string;
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

    /*
        Get the SSM Parameters
        */
    const icav2ProjectIdSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'icav2ProjectIdSsmParameterObj',
      props.icav2ProjectIdSsmParameterName
    );
    const bclconvertInteropQcUriPrefixSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'bclconvertInteropQcUriPrefixSsmParameterObj',
      props.bclconvertInteropQcUriPrefixSsmParameterName
    );
    const cttsov2OutputUriPrefixSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'cttsov2OutputUriPrefixSsmParameterObj',
      props.cttsov2OutputUriPrefixSsmParameterName
    );
    const cttsov2CacheUriPrefixSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'cttsov2CacheUriPrefixSsmParameterObj',
      props.cttsov2CacheUriPrefixSsmParameterName
    );
    const bsshOutputFastqCopyUriPrefixSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'bsshOutputFastqCopyUriPrefixSsmParameterObj',
      props.bsshOutputFastqCopyUriPrefixSsmParameterName
    );

    /*
        Call the construct        
        */
    new GlueConstruct(this, 'stacky_glue', {
      eventBusObj: eventBusObj,
      workflowManagerTableObj: workflowManagerTableObj,
      inputMakerTableObj: inputMakerTableObj,
      instrumentRunTableObj: instrumentRunTableObj,
      icav2ProjectIdSsmParameterObj: icav2ProjectIdSsmParameterObj,
      bclconvertInteropQcUriPrefixSsmParameterObj: bclconvertInteropQcUriPrefixSsmParameterObj,
      cttsov2OutputUriPrefixSsmParameterObj: cttsov2OutputUriPrefixSsmParameterObj,
      cttsov2CacheUriPrefixSsmParameterObj: cttsov2CacheUriPrefixSsmParameterObj,
      bsshOutputFastqCopyUriPrefixSsmParameterObj: bsshOutputFastqCopyUriPrefixSsmParameterObj,
    });
  }
}
