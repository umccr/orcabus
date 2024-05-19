import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Duration } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { EventRelayerConstruct } from '../../../../../components/event-workflowrunstatechange-relayer';

/*
Create an event rule for the bclconvertmanager source,
where a workflowrunstatechange detail type has occurred and the workflow is in the succeeded state.

Parse the outputs from the event into a new event object with a different source (workflowrunmanager)

The event output payload will be of the same construct.

Input Event Source: `orcabus.bclconvertmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `succeeded`

Output Event source: `orcabus.workflowrunmanager`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `complete`

*/

export interface BclconvertManagerEventHanderConstructProps {
  eventbusObj: events.EventBus;
  relayEventLambdaPath: string;
  workflowrunstatechangeLambdaLayerObj: PythonLayerVersion;
}

export class BclconvertManagerEventHanderConstruct extends Construct {
  constructor(scope: Construct, id: string, props: BclconvertManagerEventHanderConstructProps) {
    super(scope, id);

    /*
    Part 1
    Parse the outputs from the event into a new event object with a different source (workflowrunmanager)

    The event output payload will be of the same construct.

    Input Event Source: `orcabus.bclconvertmanager`
    Input Event DetailType: `orcabus.workflowrunstatechange`
    Input Event status: `succeeded`

    Output Event source: `orcabus.workflowrunmanager`
    Output Event DetailType: `orcabus.workflowrunstatechange`
    Output Event status: `complete`
    */
    const bclconvertSuccessEventRelayer = new EventRelayerConstruct(
      this,
      'bclconvertSuccessEventRelayer',
      {
        eventbusObj: props.eventbusObj,
        inputSource: 'orcabus.bclconvertmanager',
        detailType: 'workflowRunStateChange',
        inputStatus: 'succeeded',
        targetSource: 'orcabus.workflowrunmanager',
        targetStatus: 'complete',
      }
    );

    /*
    Part 2
    Input Event Source: `orcabus.workflowrunmanager`
    Input Event DetailType: `orcabus.workflowrunstatechange`
    Input Event status: `complete`

    Output Event source: `orcabus.metadatamanager`
    Output Event DetailType: `orcabus.librarystatechange`
    Output Event status: `libraryrunidsregistered`

    * The UpdateDataBaseOnNewSampleSheet Construct
      * Subscribes to the BCLConvertManagerEventHandler Stack outputs and updates the database:
        * Registers all library run ids in the samplesheet
        * Appends libraryrunids to the library ids in the samplesheet
        * For a given library id, queries the current athena database to collect metadata for the library
          * assay
          * type
          * workflow etc.
    */
    // TODO

    /*
    Part 3

    Input Event Source: `orcabus.workflowrunmanager`
    Input Event DetailType: `orcabus.workflowrunstatechange`
    Input Event status: `complete`

    Output Event source: `orcabus.bclconvertmanagerinputeventglue`
    Output Event DetailType: `orcabus.workflowrunstatechange`
    Output Event status: `complete`

    * The BsshFastqCopyManagerInputMaker Construct
      * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
      * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter
    */
    // TODO

    /*
    Part 4

    Input Event Source: `orcabus.bsshfastqcopymanagerinputeventglue`
    Input Event DetailType: `orcabus.workflowrunstatechange`
    Input Event status: `complete`

    Output Event source: `orcabus.workflowrunmanager`
    Output Event DetailType: `orcabus.workflowrunstatechange`
    Output Event status: `ready`

    * The BsshFastqCopyManagerReadyEventSubmitter Construct
      * Subscribes to the BCLConvertManagerEventHandler Stack outputs and generates a ready event for the BSSHFastqCopyManager
    */
    const bsshFastqCopyManagerReadyEventRelayer = new EventRelayerConstruct(
      this,
      'bclconvertSuccessEventRelayer',
      {
        eventbusObj: props.eventbusObj,
        inputSource: 'orcabus.bclconvertmanager',
        detailType: 'workflowRunStateChange',
        inputStatus: 'succeeded',
        targetSource: 'orcabus.workflowrunmanager',
        targetStatus: 'complete',
      }
    );
  }
}
