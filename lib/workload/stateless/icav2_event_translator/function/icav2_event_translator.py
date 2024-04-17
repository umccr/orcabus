#!/usr/bin/env python

"""
The icav2 event translator expects the following as inputs (without wrapper of eventbus)
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
import os
import json
import logging
import datetime
import boto3

events = boto3.client("events")
dynamodb = boto3.resource('dynamodb')

eventBusName = os.getenv("EVENT_BUS_NAME")
table_name = os.getenv("TABLE_NAME")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

    # Extract relevant fields from the event payload
    eventDetails = event.get("detail", {})
    logger.info(f"Received ICAv2 event: {json.dumps(eventDetails)}")
    
    projectId = eventDetails.get("projectId", '')
    eventCode = eventDetails.get("eventCode")
    analysisStatus = eventDetails.get("eventParameters", {}).get("analysisStatus", '')
    
    payload = eventDetails.get("payload", {})
    analysisId = payload.get("id", '')
    pipeline_id = payload.get("pipeline", {}).get("id",'')
    userReference = payload.get("userReference")

    # define default event tags for internal event (from payload and workflow session)
    tags = {
        "status": payload.get("status", ''),
        'payloadTags': payload.get("tags", {}),
        'workflowSessionTags': payload.get("workflowSession", {}).get("tags", {}),
        }
    
    # Check conditions for the event to be processed: 
    if (not icav2_event_checker(eventCode, analysisStatus, pipeline_id, userReference)):
        logger.error("Illegal event received. Event code, analysis status, pipeline id, user reference: ", eventCode, analysisStatus, pipeline_id, userReference)
        raise ValueError("Event does not meet ICAv2 transltor processing conditions.")
    
    # Generate internal event with required attributes
    internal_event = {
        "projectId": projectId,
        "analysisId": analysisId,
        "instrumentRunId": '_'.join(userReference.split('_')[:4]),
        "tags": tags
        }

        # send the internal event to the event bus
    response = events.put_events(
        Entries=[
            {
                "Source": 'icav2_event_translator',
                "DetailType": "ICAV2_INTERNAL_EVENT",
                "Detail": json.dumps(internal_event),
                "EventBusName": eventBusName
            }
        ]
    )
    # check if the event was successfully sent to the event bus, raise Exception if not
    if response['FailedEntryCount'] != 0:
        raise Exception("Failed to send event to the event bus.")
    
    logger.info(f"Internal event sent to the event bus. {json.dumps(internal_event)}")
    
    # Store the internal event in the DynamoDB table
    table = dynamodb.Table(table_name)
    table.put_item(
        Item={
            'id': analysisId,
            'id_type': 'icav2_analysis_id',
            'original_external_event': json.dumps(event),
            'translated_internal_event': json.dumps(internal_event),
            'timestamp': datetime.datetime.now().isoformat()
        }
    )
    
    # check if the event was successfully stored in the DynamoDB table, raise Exception if not
    if response['FailedEntryCount'] != 0:
        raise Exception("Failed to store event in the DynamoDB table.")
    
    logger.info(f"Internal event stored in the DynamoDB table.")
    return internal_event


# ICAv2 Event condition:
# eventCode is ICA_EXEC_028, 
# analysisStatus is SUCCEEDED,
# payload.pipeline.id is "bf93b5cf-cb27-4dfa-846e-acd6eb081aca", 
# and userReference matches the regex pattern
def icav2_event_checker(eventCode: str, analysisStatus: str, pipeline_id: str, userReference: str) -> bool:
    return (
        eventCode == "ICA_EXEC_028" 
        and analysisStatus == "SUCCEEDED" 
        and pipeline_id == "bf93b5cf-cb27-4dfa-846e-acd6eb081aca"
        and re.match(r"\d{6}_[A|B]\d+_\d{4}_\w+", userReference)
    )