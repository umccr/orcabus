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

events = boto3.client("events", region_name='ap-southeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
  
    assert os.getenv("EVENT_BUS_NAME"), "EVENT_BUS_NAME environment variable is not set"
    assert os.getenv("TABLE_NAME"), "TABLE_NAME environment variable is not set"
  
    eventBusName = os.getenv("EVENT_BUS_NAME")
    table_name = os.getenv("TABLE_NAME")

    # Extract relevant fields from the event payload
    eventDetails = event.get("detail", {})
    
    # Generate internal event with required attributes
    internal_event = generate_icav2_internal_event(eventDetails)

    # send the internal event to the event bus
    try:
      events.put_events(
        Entries=[
            {
                "Source": 'ocrabus.iet', # icav2 event translator
                "DetailType": "ICAV2_INTERNAL_EVENT",
                "Detail": json.dumps(internal_event),
                "EventBusName": eventBusName
            }
        ]
      )
      logger.info(f"Internal event sent to the event bus.")
    except Exception as e:
        raise Exception("Failed to send event to the event bus. Error: ", e)
    
    # Store the internal event in the DynamoDB table
    try: 
      # table = dynamodb.Table(table_name)
      dynamodb.put_item(
          TableName=table_name,
          Item={
              'id': {'S': internal_event.get("analysisId")},
              'id_type': {'S': 'icav2_analysis_id'},
              'original_external_event': {'S': json.dumps(eventDetails)},
              'translated_internal_event': {'S': json.dumps(internal_event)},
              'timestamp': {'S': datetime.datetime.now().isoformat()}
          }
      )
      logger.info(f"Original and Internal events stored in the DynamoDB table.")
    except Exception as e:
        raise Exception("Failed to store event in the DynamoDB table. Error: ", e)

    return {
        "statusCode": 200,
        "body": json.dumps("Internal event sent to the event bus and both msg stored in the DynamoDB table.")
    }

# generate ICAv2 internal event from external event
def generate_icav2_internal_event(event):
  
    projectId = event.get("projectId", '')
    eventCode = event.get("eventCode")
    analysisStatus = event.get("eventParameters", {}).get("analysisStatus", '')
    
    payload = event.get("payload", {})
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
    if (not check_icav2_event(eventCode, analysisStatus, pipeline_id, userReference)):
        logger.error("Illegal ICAV2 event received. Event code: %s, analysis status: %s, pipeline id: %s, user reference: %s", eventCode, analysisStatus, pipeline_id, userReference)
        raise ValueError("Event does not meet ICAv2 transltor processing conditions.")
    
    # Generate internal event with required attributes
    return {
        "projectId": projectId,
        "analysisId": analysisId,
        "instrumentRunId": '_'.join(userReference.split('_')[:4]),
        "tags": tags
        }
    
# Check ICAv2 Event condition:
# eventCode is ICA_EXEC_028, 
# analysisStatus is SUCCEEDED,
# payload.pipeline.id is "bf93b5cf-cb27-4dfa-846e-acd6eb081aca", 
# and userReference matches the regex pattern
def check_icav2_event(eventCode: str, analysisStatus: str, pipeline_id: str, userReference: str) -> bool:
    return (
        eventCode == "ICA_EXEC_028" 
        and analysisStatus == "SUCCEEDED" 
        and pipeline_id == "bf93b5cf-cb27-4dfa-846e-acd6eb081aca"
        and re.match(r"\d{6}_[A|B]\d+_\d{4}_\w+", userReference)
    )