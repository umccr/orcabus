# ICAv2 Event Translator

<!-- TOC -->
* [ICAv2 Event Translator](#icav2-event-translator)
  * [Inputs](#inputs)
    * [Example Input](#example-input)
  * [Outputs](#outputs)
  * [lambda function for event translation](#lambda-function-for-event-translation)
    * [Receive and Translate ICAv2 event to Orcabus internal event](#receive-and-translate-icav2-event-to-orcabus-internal-event)
    * [Save this translation to dynamoDB](#save-this-translation-process-to-dynamodb)
    * [Publish the Orcabus event to event bus](#publish-the-orcabus-event-to-event-bus)
  * [Unit Test](#unit-test)
<!-- TOC -->


## Inputs

The AWS lambda functions takes ```ICAV2_EXTERNAL_EVENT``` events with following parameters and verify specific parmaters pattern.

* eventCode is ICA_EXEC_028
* eventParameters.analysisStatus is SUCCEEDED
* payload.pipeline.id is "bf93b5cf-cb27-4dfa-846e-acd6eb081aca" - this is currently hardcoded
* Can use a regex on the userReference attribute like `(\d{6}_[A|B]\d+_\d{4}_\w+)`

### Example Input
This event is icav2 event without EventBus wrapper. General Event Bridge event will be with [standard wrapper format](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-events-structure.html) with payload in the detail.
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
  "description": "Analysis status changed",
  "projectId": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
  "payloadVersion": "v3",
  "payload": {
    "id": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
    "timeCreated": "2024-03-25T08:04:40Z",
    "timeModified": "2024-03-25T10:07:06Z",
    "ownerId": "xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
    ...
    "reference": "xxxxxx_xxxxxx_xxxxxx_xxxxxx_xxx_xxxxx-BclConvert vx_x_x-xxxxxx-xxxxxx-xxxxxx-xxxxxx-xxxxxx",
    "userReference": "xxxxxx_xxxxxx_xxxxxx_xxxxxx_xxx_xxxxxxxxxx",
    "pipeline": {
      ...
    },
    "workflowSession": {
      ...
      "status": "INPROGRESS",
      "startDate": "2024-03-25T07:57:48Z",
      "tags": {
        ...
      }
    },
    "status": "SUCCEEDED",
    "analysisStorage": {
      ....
    },
    ....
  }
}
```

## Outputs

The AWS lambda functions return ```ICAV2_INTERNAL_EVENT``` with the following parameters:

* projectId ->  "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx"
* analysisId->  "0xxxxxxx-ddxxx-xxxxx-bxx-5xxxxxxx" (payload.id)
* instrumentRunId -> "2xxxxxxxxx_Axxxxxx_0xxxx_Bxxxx" (from userReference)
* tags (payloadTags, workflow session tags)
```json5
{
  "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
  "analysisId": "0xxxxxxx-ddxxx-xxxxx-bxx-5xxxxxxx",
  "instrumentRunId": "2xxxxxxxxx_Axxxxxx_0xxxx_Bxxxx",
  "tags": {
        ...
      }
}
```

## lambda function for event translation

### Receive and Translate ICAv2 event to Orcabus internal event
Combine the iput and anylsis result to generat the orcabus internal event.

### Save this translation process to dynamoDB
Send the orignal input and orcabus event after translation to the dynao db for recording of the process. 
```json5
{
  id: analysisId,
  id_type: "icav2_analysis_id",
  original_external_event: {orignal input events},
  translated_internal_event: {orcabus event after translation},
  timestamp: datetime.datetime.now().isoformat()
}
 ```

### Publish the Orcabus event to event bus
publish the Orcabus event back the event bus.

## Unit Test

```make install```
This will install all necessary package.\
```make test```
Run unit testing for lambda function.