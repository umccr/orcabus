"""
The icav2 event translator expects the following as inputs (without envelop from sqs, event pipe, and eventbus)
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
The event tranlator then returns the following: 
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
"""

import os
import json
import logging
import datetime
import boto3
from uuid import uuid4
from translator_service.workflowrunstatechange import (
    WorkflowRunStateChange,
    AWSEvent,
    Marshaller,
)

events = boto3.client("events", region_name='ap-southeast-2')
dynamodb = boto3.client('dynamodb', region_name='ap-southeast-2')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
  
    assert os.getenv("EVENT_BUS_NAME"), "EVENT_BUS_NAME environment variable is not set"
    assert os.getenv("TABLE_NAME"), "TABLE_NAME environment variable is not set"
  
    event_bus_name = os.getenv("EVENT_BUS_NAME")
    table_name = os.getenv("TABLE_NAME")

    # Extract relevant fields from the event payload
    event_details = event.get("detail", {}).get("ica-event", {})
    
    # Generate internal AWS event (orcabus.wfm@WorkflowRunStateChange)
    internal_ica_event = translate_to_aws_event(event_details)

    # send the internal event to the event bus
    try:
      events.put_events(
        Entries=[
            {
                "Source": internal_ica_event.source,
                "DetailType": internal_ica_event.detail_type,
                "Detail": json.dumps(Marshaller.marshall(internal_ica_event.detail)),
                "EventBusName": event_bus_name
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
              'analysis_id': {'S': internal_ica_event.detail.payload.get("analysisId", '')},
              'event_status': {'S': internal_ica_event.detail.status},
              'id_type': {'S': 'analysis_id'},
              "portal_run_id": {'S': internal_ica_event.detail.portalRunId},
              'original_external_event': {'S': json.dumps(event_details)},
              'translated_internal_ica_event': {'S': json.dumps(internal_ica_event.detail.to_dict())},
              'timestamp': {'S': internal_ica_event.detail.timestamp}
          }
      )
      logger.info(f"Original and Internal events stored in the DynamoDB table.")
    except Exception as e:
        raise Exception("Failed to store event in the DynamoDB table. Error: ", e)

    return {
        "statusCode": 200,
        "body": json.dumps("Internal event sent to the event bus and both msg stored in the DynamoDB table.")
    }

# Convert from Entity model to aws event object with aws event envelope
def translate_to_aws_event(event)->AWSEvent:
  return AWSEvent(
    detail= get_event_details(event),
    detail_type= "WorkflowRunStateChange",
    # version="0.1.0",  # comment as the version is managed by the evnet bus
    source= "orcabus.bcm",
  )

# Convert from entity module to internal event details
def get_event_details(event)->WorkflowRunStateChange:
    # Extract relevant fields from the event payload
    project_id = event.get("projectId", '')
    analysis_status = event.get("eventParameters", {}).get("analysisStatus", '')
    
    payload = event.get("payload", {})
    pipeline = payload.get("pipeline", {})
    
    # generate internal event with required attributes
    return WorkflowRunStateChange(
      portal_run_id= get_portal_run_id(payload.get("id", '')),
      timestamp= datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
      status= analysis_status,
      workflow_type= "bssh_bcl_convert",
      workflow_version= "4.2.7",
      payload= {
        "refId": None,
        "version": "0.1.0",
        "projectId": project_id,
        "analysisId": payload.get("id", ''),
        "userReference": payload.get("userReference", ''),
        "timeCreated": payload.get("timeCreated",""),
        "timeModified": payload.get("timeModified",""),
        "pipelineId": pipeline.get("id",''),
        "pipelineCode": pipeline.get("code",''),
        "pipelineDescription": pipeline.get("description",''),
        "pipelineUrn": pipeline.get("urn",'')
      }
    )

# check the dynamodb table to see if new portal run id is required
def get_portal_run_id(analysis_id: str) -> str:
    
    # check if dynomodb table have the anylsis id
    table_name = os.getenv("TABLE_NAME")
    try:
      response = dynamodb.scan(
        TableName=table_name,
        FilterExpression='analysis_id = :analysis_id',
        ExpressionAttributeValues={
          ':analysis_id': {'S': analysis_id }
        }
      )
      items = response.get('Items', [])
      # check if the response.Items has items
      if items:
        logger.info(f"Analysis ID already exists in the DynamoDB table.")
        return items[0].get("portal_run_id").get("S")
      else:
        return generate_portal_run_id()
      
    except Exception as e:
      raise Exception("Failed to get item from the DynamoDB table. Error: ", e)
    
def generate_portal_run_id():
        return f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}{str(uuid4())[:8]}"
