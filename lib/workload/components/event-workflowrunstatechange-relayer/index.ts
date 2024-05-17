import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Duration } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import path from 'path';
import { PythonWorkflowrunstatechangeLambdaLayerConstruct } from '../python-workflowrunstatechange-lambda-layer';

/*
Useful for relaying an event from an external service (such as an icav2 service),
to the workflowRunManager to say that a workflow has completed
*/

export interface EventRelayerConstructProps {
  eventbusObj: events.EventBus;
  detailType: string;
  inputSource: string;
  inputStatus: string;
  targetSource: string;
  targetStatus: string;
}

export class EventRelayerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: EventRelayerConstructProps) {
    super(scope, id);

    // Create a rule for the event
    // Trigger state machine on event
    const rule = new events.Rule(this, 'bclconvertmanagereventhandlerrule', {
      eventBus: props.eventbusObj,
      eventPattern: {
        source: [props.inputSource],
        detailType: [props.detailType],
        detail: {
          // ignore case on status
          status: [props.inputStatus],
        },
      },
    });
    const workflowrunstatechangeLambdaLayerObj: PythonLayerVersion =
      new PythonWorkflowrunstatechangeLambdaLayerConstruct(this, 'event_layer_lambda_layer', {})
        .lambdaLayerVersionObj;

    // Create lambda to repush the event from the bclconvertmanager source to the workflowrunmanager source
    const lambdaFunction = new PythonFunction(this, 'relay_lambda', {
      entry: path.join('__dirname', 'relay_event_with_new_source_lambda_py'),
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      index: 'relay_event_with_new_source_lambda.py',
      handler: 'handler',
      memorySize: 1024,
      layers: [workflowrunstatechangeLambdaLayerObj],
      timeout: Duration.seconds(60),
      environment: {
        EVENT_BUS_NAME: props.eventbusObj.eventBusName,
        OUTPUT_EVENT_SOURCE: props.targetSource,
        OUTPUT_EVENT_DETAIL_TYPE: props.detailType,
        OUTPUT_EVENT_STATUS: props.targetStatus,
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(new events_targets.LambdaFunction(lambdaFunction));

    // Allow the lambdafunction to submit events to the event bus
    props.eventbusObj.grantPutEventsTo(<iam.Role>lambdaFunction.currentVersion.role);
  }
}
