"""
The icav2 event translator expects the following as inputs (without wrapper from sqs, event pipe, and eventbus)
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
    "portalRunId": "202405012397actg",
    "timestamp": "2024-05-01T09:25:44Z",
    "status": "succeeded",
    "workflowType": "bssh_bcl_convert",
    "workflowVersion": "4.2.7",
    "payload": {
      "refId": null,
      "version": "0.1.0",
      "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
      "analysisId": "aaaaafe8-238c-4200-b632-d5dd8c8db94a",
      "userReference": "540424_A01001_0193_BBBBMMDRX5_c754de_bd822f",
      "timeCreated": "2024-05-01T10:11:35Z",
      "timeModified": "2024-05-01T11:24:29Z",
      "pipelineId": "bfffffff-cb27-4dfa-846e-acd6eb081aca",
      "pipelineCode": "BclConvert v4_2_7",
      "pipelineDescription": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
      "pipelineUrn": "urn:ilmn:ica:pipeline:bfffffff-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7"
    },
    "serviceVersion": "0.1.0"
  }
"""

import os
import json
import logging
import datetime
import boto3
from uuid import uuid4
from function.workflowrunstatechange import (
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
    version="0.1.0",
    source= "orcabus.bct",
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
