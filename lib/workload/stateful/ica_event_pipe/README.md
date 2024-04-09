# ICA Event Pipe

This stack creates the necessary infrastructure to allow external (ICA) events to flow on to an internal Event Bus.


## IcaEventPipeStack

This stack is a light-weight wrapper around the IcaEventPipeConstruct


### IcaEventPipeStackProps

- **name**:				The name for stack
- **eventBusName**:		The name of the Event Bus to forward events to (used to lookup the Event Bus)
- **slackTopicName**:	The name of the SNS Topic to receive DLQ notifications from CloudWatch

Note: the stack defines sensible values for the other construct parameters.


## IcaEventPipeConstruct

A single construct that has:
- an SQS queue to receive the incoming external events
- a corresponding DLQ for the SQS queue
- a CloudWatch Alarm that is triggered when events are moved to the DLQ and that sends events to an existing SNS Topic
- an Event Pipe to forward the incoming events from the SQS queue to the Event Bus
- an Input Transformation to remove the SQS envelop when forwarding external events to the bus
  
This construct makes use of the [sqs-dlq-monitoring](https://constructs.dev/packages/sqs-dlq-monitoring/v/1.2.3?lang=typescript) constuct from [ConstuctHub](https://constructs.dev/).


### IcaEventPipeConstructProps

Configuration / Properties of the construct.

- **icaEventPipeName**:		The name for the Event Pipe
- **icaQueueName**:			The name for the incoming SQS queue (the DLQ with use this name with a "-dlq" postfix)
- **icaQueueVizTimeout**:	The visibility timeout for the queue
- **eventBusName**:			The name of the Event Bus to forward events to (used to lookup the Event Bus)
- **slackTopicArn**:		The ARN of the SNS Topic to receive DLQ notifications from CloudWatch
- **dlqMessageThreshold**:	The CloudWatch Alarm threshold to use before raising an alarm