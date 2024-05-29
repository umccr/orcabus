import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { fastqListRowsToCttsov2InputMakerConstruct } from './constructs/part_1/fastq-list-rows-to-cttsov2-input-maker';
import { cttsov2InputMakerConstruct } from './constructs/part_2/cttsov2-input-maker';
import { cttsov2ManagerReadyEventHandlerConstruct } from './constructs/part_3/cttsov2-ready-event-handler';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface cttsov2GlueHandlerConstructProps {
  eventBusObj: events.IEventBus;
  instrumentRunTableObj: dynamodb.ITableV2;
  inputMakerTableObj: dynamodb.ITableV2;
  workflowManagerTableObj: dynamodb.ITableV2;
  cttsov2OutputUriPrefixSsmParameterObj: ssm.IStringParameter;
  cttsov2CacheUriPrefixSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class cttsov2GlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: cttsov2GlueHandlerConstructProps) {
    super(scope, id);

    /*
        Part 1
        Input Event Source: `orcabus.instrumentrunmanager`
        Input Event DetailType: `LibraryStateChange`
        Input Event status: `fastqlistrowregistered`

        Output Event source: `orcabus.cttsov2inputeventglue`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `awaitinginput`

       */
    const fastqListRowsToctTSOv2InputMaker = new fastqListRowsToCttsov2InputMakerConstruct(
      this,
      'fastq_list_rows_to_cttso_v2_input_maker',
      {
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        instrumentRunTableObj: props.instrumentRunTableObj,
        outputUriPrefixSsmParameterObj: props.cttsov2OutputUriPrefixSsmParameterObj,
        eventBusObj: props.eventBusObj,
        tableObj: props.inputMakerTableObj,
      }
    );

    /*
        Part 2

        Input Event source: `orcabus.cttsov2inputeventglue`
        Input Event DetailType: `WorkflowRunStateChange`
        Input Event status: `awaitinginput`

        Output Event source: `orcabus.cttsov2inputeventglue`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `ready`

        * The ctTSOv2InputMaker Construct
          * Subscribes to the FastqListRowEventHandler Construct outputs and creates the input for the ctTSOv2ReadySfn
          * Pushes an event payload of the input for the ctTSOv2ReadyEventSubmitters
          * From the awaiting input event, we then generate a workflow ready status for each of the cttso run workflows

        */

    const ctTSOv2InputMaker = new cttsov2InputMakerConstruct(this, 'cttso_v2_input_maker', {
      cacheUriPrefixSsmParameterObj: props.cttsov2CacheUriPrefixSsmParameterObj,
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      outputUriPrefixSsmParameterObj: props.cttsov2OutputUriPrefixSsmParameterObj,
      eventBusObj: props.eventBusObj,
      tableObj: props.instrumentRunTableObj,
    });

    /*
        Part 3

        Input Event Source: `orcabus.cttsov2inputeventglue`
        Input Event DetailType: `WorkflowRunStateChange`
        Input Event status: `ready`

        Output Event source: `orcabus.workflowmanager`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `ready`

        * The cttsov2ReadyEventSubmitter Construct
          * Subscribes to the cttsov2ReadyEventSubmitter Construct outputs and generates a ready event for the cttsov2 ICAv2 workflow

        */
    // const ctTSOv2InputReadyEvent = new cttsov2ManagerReadyEventHandlerConstruct(
    //   this,
    //   'cttsov2_ready_event_submitter',
    //   {
    //     eventBusObj: props.eventBusObj,
    //     tableObj: props.workflowManagerTableObj,
    //   }
    // );
  }
}
