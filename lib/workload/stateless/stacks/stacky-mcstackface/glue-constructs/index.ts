import {Construct} from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import {BclconvertManagerEventHandlerConstruct} from "./selleys";
import {cttsov2GlueHandlerConstruct} from "./super";


/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface glueConstructProps {
    /* Event Bus */
    eventBusObj: events.EventBus;
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

export class glueConstruct extends Construct {
    constructor(scope: Construct, id: string, props: glueConstructProps) {
        super(scope, id);

        /*
        Part A: Glue the bclconvertmanager success event to the bsshFastqCopyManager
        */
        const scotch = new BclconvertManagerEventHandlerConstruct(
            this,
            'scotch',
            {
                /* Event Bus */
                eventBusObj: props.eventBusObj,
                /* Tables */
                workflowManagerTableObj: props.workflowManagerTableObj,
                inputMakerTableObj: props.inputMakerTableObj,
                instrumentRunTableObj: props.instrumentRunTableObj,
                /* SSM Parameters */
                bclconvertInteropQcUriPrefixSsmParameterObj: props.bclconvertInteropQcUriPrefixSsmParameterObj,
                icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
            }
        );

        /*
        Part B: Connect the bsshFastqCopyManager completion to the BCLConvert InterOp QC Manager
        */
        const selleys = new BclconvertManagerEventHandlerConstruct(
            this,
            'selleys',
            {
                /* Event Bus */
                eventBusObj: props.eventBusObj,
                /* Tables */
                workflowManagerTableObj: props.workflowManagerTableObj,
                inputMakerTableObj: props.inputMakerTableObj,
                instrumentRunTableObj: props.instrumentRunTableObj,
                /* SSM Parameters */
                bclconvertInteropQcUriPrefixSsmParameterObj: props.bclconvertInteropQcUriPrefixSsmParameterObj,
                icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
            }
        );


        /*
        Part C: Connect the BSSH Copy Completion to the cttsov2Manager
        */
        const super_glue = new cttsov2GlueHandlerConstruct(
            this,
            'super',
            {
                /* Event Bus */
                eventBusObj: props.eventBusObj,
                /* Tables */
                workflowManagerTableObj: props.workflowManagerTableObj,
                inputMakerTableObj: props.inputMakerTableObj,
                instrumentRunTableObj: props.instrumentRunTableObj,
                /* SSM Parameters */
                icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
                cttsov2OutputUriPrefixSsmParameterObj: props.cttsov2OutputUriPrefixSsmParameterObj,
                cttsov2CacheUriPrefixSsmParameterObj: props.cttsov2CacheUriPrefixSsmParameterObj
            }
        );
    }
}
