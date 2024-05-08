# ICA Event Translator

This stack creates the ica event translator service to translate external (ICA) events to orcabus events follow the defined schema `orcabus.wfm@WorkflowRunStateChange`. Example event can be seen [here](../../../../../../docs/event-schemas/wfm/example/WRSC__bct__bssh_bcl_convert.json). 


<!-- TOC -->
* [ICAv2 Event Translator](#icav2-event-translator)
  * [Inputs](#inputs)
    * [Example ICA Event Input](#example-ica-event-input)
  * [Outputs](#outputs)
  * [lambda function for event translation](#lambda-function-for-event-translation)
    * [Receive and Translate ICAv2 event to Orcabus internal event](#receive-and-translate-icav2-event-to-orcabus-internal-event)
    * [Save this translation to dynamoDB](#save-this-translation-process-to-dynamodb)
    * [Publish the Orcabus event to event bus](#publish-the-orcabus-event-to-event-bus)
  * [Unit Test](#unit-test)
<!-- TOC -->


## Inputs

The AWS lambda functions takes ```External ICA Event``` events with following envelope pattern (sqs, event pipe). 

>AWS Pipes doesn't directly allow overriding the `source` and `detail-type` at the Pipe level because these are set by the AWS Pipes framework itself when routing events through Pipes. 

```json5
{
  "version": "0",
  "id": "3xxxxxx-fxxxxx-2xxx-axxx-cxxxxxxxx",
  "detail-type": "Event from aws:sqs", // event from sqs event pipeline
  "source": "Pipe IcaEventPipeName", // source from Pipe {IcaEventPipeName}
  "account": "xxxxxxxxx",
  "time": "2024-00-00T00:01:00Z",
  "region": "ap-southeast-x",
  "resources": [],
  "detail": {
    "ica-event": ['*'] // ica event payload
  }
}
```

### Example Ica Event Input
This event is icav2 event without EventBus pipe envelop. General Event Bridge event will be with [standard wrapper format](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-events-structure.html) with payload in the detail.
```json5
{
  "correlationId": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
  "timestamp": "2024-03-25T10:07:09.990Z",
  "eventCode": "IXX_EXXX_XXX",
  "eventParameters": {
    "pipelineExecution": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
    "analysisPreviousStatus": "INPROGRESS",
    "analysisStatus": "SUCCEEDED"
  },
  "projectId": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
  "payload": {
    "id": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
    "timeCreated": "2024-00-25T00:04:00Z",
    "timeModified": "2024-00-25T00:07:00Z",
    "userReference": "xxxxxx_xxxxxx_xxxxxx_xxxxxx_xxx_xxxxxxxxxx",
    ...
    "pipeline": {
      "id": "bxxxx-cxxx-4xxx-8xxxx-axxxxxxxxxxx",
      "timeCreated": "2024-00-00T01:16:50Z",
      "timeModified": "2024-00-00T02:08:46Z",
      "code": "BclConvert v0_0_0",
      "urn": "urn:ilmn:ica:pipeline:bxxxx-cxxx-4xxx-8xxxx-axxxxxxxxxxx#BclConvert_v0_0_0",
      "description": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
      ...
    },
    ....
  }
}
```

## Outputs

The AWS lambda functions return ```WorkflowRunStateChange``` with the following parameters:

```json5
{
  "version": "0", // by default is 0
  "id": "dxxxxx-6xxxx-fxxx-1xxx-5xxxxx",
  "detail-type": "WorkflowRunStateChange", // event type
  "source": "orcabus.bct", // from bct service
  "account": "404687356768",
  "time": "2024-00-00T02:08:46Z",
  "region": "ap-southeast-x",
  "resources": [],
  "detail": {
    // tranalted event deatils (see below)
  }
}
```
Internal WorkflowRunStateChange event detail:
```json5
{
  "portalRunId": '20xxxxxxxxxx',
  "timestamp": "2024-00-25T00:07:00Z",
  "status": "SUCCEEDED",
  "workflowType": "bssh_bcl_convert",
  "workflowVersion": "4.2.7",
  "payload": {
    "refId": None,
    "version": "0.1.0",
    "projectId": "valid_project_id",
    "analysisId": "valid_payload_id",
    "userReference": "123456_A1234_0000_TestingPattern",
    "timeCreated": "2024-01-01T00:11:35Z",
    "timeModified": "2024-01-01T01:24:29Z",
    "pipelineId": "valid_pipeline_id",
    "pipelineCode": "BclConvert v0_0_0",
    "pipelineDescription": "BclConvert pipeline.",
    "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0"
  }
}
```

## lambda function for event translation

### Receive and Translate ICAv2 event to Orcabus internal event
Combine the iput and anylsis result to generat the orcabus internal event.
Event Pattern (filter rules) for event pipe:
```json5
{
  account: [Stack.of(this).account],
  detailType: ['Event from aws:sqs'],
  source: [`Pipe {props.icaEventPipeName}`],
  detail: {
      'ica-event': {
        eventCode: [{ prefix: 'ICA_EXEC_' }],
        projectId: [{ exists: true }],
        payload: [{ exists: true }],
        ...
      },
  },
}
```

### Save this translation process to dynamoDB
Send the orignal input and orcabus event after translation to the dynao db for recording of the process. 

Dynamodb format:
| analysis_id    | event_status | id_type | portal_run_id | original_external_event | translated_internal_ica_event | timestamp |
| -------- | ------- | ------- | ------- | ------- | ------- |------- | 
| dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | PREPARING_INPUTS | analysis_id | 20xxxxxxxxxx | {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | SUCCEEDED  | analysis_id | 20xxxxxxxxxx | {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |


### Publish the Orcabus event to event bus
publish the Orcabus (internal) event back the event bus.
Example output event can be seen [here](../../../../../../docs/event-schemas/wfm/example/WRSC__bct__bssh_bcl_convert.json).

## Unit Test

```make install```
This will install all necessary package.\
```make test```
Run unit testing for lambda function.