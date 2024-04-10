#!/usr/bin/env python

"""
The icav2 event translator expects the following as inputs

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
      "summary": "",
      "tags": {
        ...
      }
    },
    "status": "SUCCEEDED",
    "startDate": "2024-03-25T08:04:51Z",
    "endDate": "2024-03-25T10:07:05Z",
    "summary": "",
    "analysisStorage": {
      ....
    },
    ....
  }
}


The event tranlator then returns the following

{
  "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
  "analysisId": "0xxxxxxx-ddxxx-xxxxx-bxx-5xxxxxxx",
  "instrumentRunId": "2xxxxxxxxx_Axxxxxx_0xxxx_Bxxxx",
  
  "tags": {
        ...
      }
}

"""
import re

def icav2_event_translator_handler(event, context):

    # Extract relevant fields from the event payload
    projectId = event.get("projectId")
    eventCode = event.get("eventCode")
    eventParameters = event.get("eventParameters", {})
    analysisStatus = eventParameters.get("analysisStatus")
    payload = event.get("payload", {})
    analysisId = payload.get("id")
    pipeline_id = payload.get("pipeline", {}).get("id")
    userReference = payload.get("userReference")
    
    # define event tags for internal event (from workflow session)
    tags = payload.get("workflowSession", {}).get("tags", {})

    # Check conditions for the event to be processed: 
    # eventCode is ICA_EXEC_028, analysisStatus is SUCCEEDED,
    # payload.pipeline.id is "bf93b5cf-cb27-4dfa-846e-acd6eb081aca", 
    # and userReference matches the regex pattern
    if (
        eventCode == "ICA_EXEC_028" 
        and analysisStatus == "SUCCEEDED" 
        and pipeline_id == "bf93b5cf-cb27-4dfa-846e-acd6eb081aca" 
        and re.match(r"\d{6}_[A|B]\d+_\d{4}_\w+", userReference)
    ):
        # Generate internal event with required attributes
        internal_event = {
            "projectId": projectId,
            "analysisId": analysisId,
            "instrumentRunId": '_'.join(userReference.split('_')[:4]),
            "tags": tags
        }
        
        # For now, just return the internal event
        return internal_event
    else:
        # Conditions not met, throw an error
        raise ValueError("Event does not meet processing conditions.")
