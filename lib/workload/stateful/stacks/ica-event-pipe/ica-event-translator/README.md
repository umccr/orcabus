# ICA Event Translator

This stack creates the ica event translator service to translate external (ICA) events to orcabus events follow the defined schema `orcabus.wfm@WorkflowRunStateChange`. Example event can be seen [here](../../../../../../docs/event-schemas/wfm/example/WRSC__bct__bssh_bcl_convert.json). 


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

* project_id ->  "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx"
* analysis_id->  "0xxxxxxx-ddxxx-xxxxx-bxx-5xxxxxxx" (payload.id)
* instrument_run_id -> "2xxxxxxxxx_Axxxxxx_0xxxx_Bxxxx", (from userReference)
* portal_run_id ???
* output_uri_prefix ???
* tags (payloadTags, workflow session tags)
```json5
{
  "project_id": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
  "analysis_id": "0xxxxxxx-ddxxx-xxxxx-bxx-5xxxxxxx",
  "instrument_run_id": "2xxxxxxxxx_Axxxxxx_0xxxx_Bxxxx",
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
publish the Orcabus (internal) event back the event bus.

## Unit Test

```make install```
This will install all necessary package.\
```make test```
Run unit testing for lambda function.