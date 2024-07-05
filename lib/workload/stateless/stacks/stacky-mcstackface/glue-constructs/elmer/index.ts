import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BsshFastqCopyManagerInputMakerConstruct } from './part_1/bssh-fastq-copy-manager-input-maker';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface BclconvertToBsshFastqCopyEventHandlerConstructProps {
  eventBusObj: events.IEventBus;
  inputMakerTableObj: dynamodb.ITableV2;
  bsshOutputFastqCopyUriPrefixSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
}

export class BclconvertToBsshFastqCopyEventHandlerConstruct extends Construct {
  constructor(
    scope: Construct,
    id: string,
    props: BclconvertToBsshFastqCopyEventHandlerConstructProps
  ) {
    super(scope, id);
    /*
        Part 1

        Input Event Source: `orcabus.workflowmanager`
        Input Event DetailType: `WorkflowRunStateChange`
        Input Event status: `complete`

        Output Event source: `orcabus.bclconvertmanagerinputeventglue`
        Output Event DetailType: `WorkflowRunStateChange`
        Output Event status: `complete`

        * The BsshFastqCopyManagerInputMaker Construct
          * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
          * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter
        */
    const bsshFastqCopyManagerInputMaker = new BsshFastqCopyManagerInputMakerConstruct(
      this,
      'bssh_fastq_copy_input_maker',
      {
        eventBusObj: props.eventBusObj,
        outputUriPrefixSsmParameterObj: props.bsshOutputFastqCopyUriPrefixSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        tableObj: props.inputMakerTableObj,
      }
    );
  }
}
