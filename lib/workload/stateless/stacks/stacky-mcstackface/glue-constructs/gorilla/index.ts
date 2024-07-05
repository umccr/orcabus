import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BclconvertInteropqcInputMakerConstruct } from './part_1/bclconvert-interop-qc-input-maker';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface BsshFastqCopyToBclconvertInteropQcConstructProps {
  /* Event Objects */
  eventBusObj: events.IEventBus;
  /* Table Objects */
  inputMakerTableObj: dynamodb.ITableV2;
  /* SSM Parameter Ojbects */
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class BsshFastqCopyToBclconvertInteropQcConstruct extends Construct {
  constructor(
    scope: Construct,
    id: string,
    props: BsshFastqCopyToBclconvertInteropQcConstructProps
  ) {
    super(scope, id);

    /*
    Part 1

    Input Event Source: `orcabus.workflowmanager`
    Input Event DetailType: `WorkflowRunStateChange`
    Input Event status: `complete`

    Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
    Output Event DetailType: `WorkflowRunStateChange`
    Output Event status: `complete`

    * The BCLConvertInteropQCInputMaker Construct
      * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
      * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter
    */
    const bclconvertInteropqcInputMaker = new BclconvertInteropqcInputMakerConstruct(
      this,
      'bclconvert_interopqc_input_maker',
      {
        eventBusObj: props.eventBusObj,
        analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
        analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
        tableObj: props.inputMakerTableObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      }
    );
  }
}
