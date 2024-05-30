# BclConvert Manager

This stack creates the BclConvert Manager service which include ica event translator service to translate external (ICA) events to orcabus events follow the defined schema `orcabus.bclconvertmanager@WorkflowRunStateChange`. Example event can be seen [here](../../../../../docs/schemas/events/executionservice/example/WRSC__example1.json).

## Icav2 event translator service

<!-- TOC -->
* [Icav2 Event Translator](#icav2-event-translator-service)
  * [Inputs](#inputs)
    * [Example ICA Event Input](#example-ica-event-input)
  * [Outputs](#outputs)
  * [lambda function for event translation](#lambda-function-for-event-translation)
    * [Receive and Translate ICAv2 event to Orcabus internal event](#receive-and-translate-icav2-event-to-orcabus-internal-event)
    * [Save this translation to dynamoDB](#save-this-translation-process-to-dynamodb)
    * [Publish the Orcabus event to event bus](#publish-the-orcabus-event-to-event-bus)
  * [Unit Test](#unit-test)
<!-- TOC -->

### Inputs

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
    "ica-event": {} // ica event payload
  }
}
```

#### Example Ica Event Input

This event is icav2 event without EventBus pipe envelop. General Event Bridge event will be with [standard wrapper format](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-events-structure.html) with payload in the detail.

``` json5
{
  "correlationId": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
  "timestamp": "2024-03-25T10:07:09.990Z",
  "eventCode": "ICA_EXEC_028",
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

### Outputs

The AWS lambda functions put translated event following  ```WorkflowRunStateChange``` schema with the following event detail::

(Non-SUCCEEDED Event without payload)

```json5
{
  "version": "0",
  "id": "f71aaaaa-5b36-40c2-f7dc-804ca6270cd6",
  "detail-type": "WorkflowRunStateChange",
  "source": "orcabus.bclconvertmanager",
  "account": "123456789012",
  "time": "2024-05-01T09:25:44Z",
  "region": "ap-southeast-2",
  "resources": [],
  "detail": {
    "portalRunId": '20xxxxxxxxxx',
    "executionId": "valid_payload_id",
    "timestamp": "2024-00-25T00:07:00Z",
    "status": "INPROGRESS",
    "workflowName": "BclConvert",
    "workflowVersion": "4.2.7",
    "workflowRunName": "123456_A1234_0000_TestingPattern",
  }
}
```

(SUCCEEDED Event)

```json5
{
  "version": "0",
  "id": "f71aaaaa-5b36-40c2-f7dc-804ca6270cd6",
  "detail-type": "WorkflowRunStateChange",
  "source": "orcabus.bclconvertmanager",
  "account": "123456789012",
  "time": "2024-05-01T09:25:44Z",
  "region": "ap-southeast-2",
  "resources": [],
  "detail": {
    "portalRunId": "202405012397actg",
    "timestamp": "2024-05-01T09:25:44Z",
    "status": "SUCCEEDED",
    "workflowName": "BclConvert",
    "workflowVersion": "4.2.7",
    "workflowRunName": "540424_A01001_0193_BBBBMMDRX5_c754de_bd822f",
    "payload": {
      "version": "0.1.0",
      "data": {
        "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
        "analysisId": "aaaaafe8-238c-4200-b632-d5dd8c8db94a",
        "userReference": "540424_A01001_0193_BBBBMMDRX5_c754de_bd822f",
        "timeCreated": "2024-05-01T10:11:35Z",
        "timeModified": "2024-05-01T11:24:29Z",
        "pipelineId": "bfffffff-cb27-4dfa-846e-acd6eb081aca",
        "pipelineCode": "BclConvert v4_2_7",
        "pipelineDescription": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
        "pipelineUrn": "urn:ilmn:ica:pipeline:bfffffff-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7",
        "instrumentRunId": "12345_A12345_1234_ABCDE12345",
        "basespaceRunId": "1234567",
        "samplesheetB64gz": "H4sIAFGBVWYC/9VaUW+jOBD+Kyvu9VqBgST0njhWh046..."
      }
    }
  }
}
```

### lambda function for event translation

#### Receive and Translate ICAv2 event to Orcabus internal event

Combine the iput and anylsis result to generat the orcabus internal event.
Event Pattern (filter rules) for event pipe:

```json5
{
  account: [Stack.of(this).account],
  detail: {
    'ica-event': {
    eventCode: ['ICA_EXEC_028'],
    projectId: [{ exists: true }],
    payload: {
        pipeline: {
          code: [{ prefix: 'BclConvert' }],
        },
      },
    },
  },
}
```

#### Save this translation process to dynamoDB

Send the orignal input and orcabus event after translation to the dynamo db for audit or recording of the process.

Dynamodb format:
| id | id_type | analysis_id | analysis_status | portal_run_id | db_uuid | original_external_event | translated_internal_ica_event | timestamp |
| -------- | ---- | ------- | ------- | ---- | ------- | ------- | ------- |------- |
| 20xxxxxxxxxx | portal_run_id | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | | | 4xxxxx-4xxxx-4xxx-4xxx-4xxxxx | | | |
| dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | analysis_id |  |   | 20xxxxxxxxxx | 4xxxxx-4xxxx-4xxx-4xxx-4xxxxx | | | |
| 1xxxxx-1xxxx-1xxx-1xxx-1xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | INITIALIZING | 20xxxxxxxxxx | | {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|2xxxxx-2xxxx-2xxx-2xxx-2xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | QUEUED | 20xxxxxxxxxx | |  {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|3xxxxx-3xxxx-3xxx-3xxx-3xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | IN_PROGRESS | 20xxxxxxxxxx | |  {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |
|4xxxxx-4xxxx-4xxx-4xxx-4xxxxx | db_uuid | dxxxxx-6xxxx-fxxx-1xxx-5xxxxx | SUCCEEDED | 20xxxxxxxxxx | |  {"correlationId": "",...} | {'portal_run_id': "",...} | 2024-01-01T00:11:35Z |

#### Publish the Orcabus event to event bus

publish the Orcabus (internal) event back the event bus.
Example output event can be seen [here](../../../../../docs/event-schemas/bclconvertmanager/example/WRSC__bcm__bssh_bcl_convert.json).

### Unit Test

Move to bclconvert-manager/translator_service, test script: [`test_icav2_event_translator.py`](./translator_service/tests/test_icav2_event_translator.py)

```make install```
This will install all necessary package.\
```make test```
Run unit testing for lambda function.

> **_NOTE:_**: This unit test only cover logic in icav2_event_translator.py not boto3.client service. All boto3.client service and ica api call will be mocked by Stubber.
