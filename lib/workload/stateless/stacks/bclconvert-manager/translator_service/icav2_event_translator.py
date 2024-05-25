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
    "data": {
        "projectId": "valid_project_id",
        "analysisId": "valid_payload_id",
        "userReference": "123456_A1234_0000_TestingPattern",
        "timeCreated": "2024-01-01T00:11:35Z",
        "timeModified": "2024-01-01T01:24:29Z",
        "pipelineId": "valid_pipeline_id",
        "pipelineCode": "BclConvert v0_0_0",
        "pipelineDescription": "BclConvert pipeline.",
        "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0",
        "instrumentRunId": "valid_instrument_run_id",
        "basespaceRunId": "1234567"
        "samplesheetB64gz": "B64Compressed SampleSheetJSON"
    }
  }
}
"""

# Standard imports
import os
import json
import logging
from datetime import datetime, timezone
import boto3
from uuid import uuid4
from uuid6 import uuid7
import typing

# Layer imports
from workflowrunstatechange import (
    WorkflowRunStateChange,
    AWSEvent,
    Marshaller,
)

# Local imports
from .icav2_analysis import collect_analysis_objects

# For IDE only
if typing.TYPE_CHECKING:
    from mypy_boto3_events.client import EventBridgeClient
    from mypy_boto3_dynamodb.client import DynamoDBClient


def get_events_client() -> 'EventBridgeClient':
    return boto3.client("events")


def get_dynamodb_client() -> 'DynamoDBClient':
    return boto3.client("dynamodb")


# Set loggers
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    # Assert env vars
    assert os.getenv("EVENT_BUS_NAME"), "EVENT_BUS_NAME environment variable is not set"
    assert os.getenv("TABLE_NAME"), "TABLE_NAME environment variable is not set"

    event_bus_name = os.getenv("EVENT_BUS_NAME")
    table_name = os.getenv("TABLE_NAME")

    # Extract relevant fields from the event payload
    event_details = event.get("detail", {}).get("ica-event", {})

    # Generate internal AWS event (orcabus.wfm@WorkflowRunStateChange)
    internal_ica_event = translate_to_aws_event(event_details)

    # Get boto3 clients
    events = get_events_client()
    dynamodb = get_dynamodb_client()

    # send the internal event to the event bus
    try:
        events.put_events(
            Entries=[
                {
                    "Source": str(internal_ica_event.source),
                    "DetailType": str(internal_ica_event.detail_type),
                    "Detail": json.dumps(Marshaller.marshall(internal_ica_event.detail)),
                    "EventBusName": str(event_bus_name)
                }
            ]
        )
        logger.info(f"Internal event sent to the event bus.")
    except Exception as e:
        raise Exception("Failed to send event to the event bus. Error: ", e)

    # Store the internal event in the DynamoDB table
    try:
        db_uuid = generate_db_uuid()
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'id': {'S': db_uuid},
                'id_type': {'S': 'db_uuid'},
                'analysis_id': {'S': internal_ica_event.detail.payload.get("analysisId", '')},
                'analysis_status': {'S': internal_ica_event.detail.status},
                # 'SUCCEEDED', 'FAILED', 'INPROGRESS', 'ABORTED', 'UNKNOWN
                "portal_run_id": {'S': internal_ica_event.detail.portalRunId},
                'original_external_event': {'S': json.dumps(event_details)},
                'translated_internal_ica_event': {'S': json.dumps(internal_ica_event.detail.to_dict())},
                'timestamp': {'S': internal_ica_event.detail.timestamp}
            }
        )
        logger.info(f"Original and Internal events stored in the DynamoDB table.")

        # update dynamodb table with the new generate db_uuid
        dynamodb.update_item(
            TableName=table_name,
            Key={
                'id': {'S': internal_ica_event.detail.payload.get("analysisId", '')},
                'id_type': {'S': 'analysis_id'}
            },
            UpdateExpression='SET db_uuid = :db_uuid',
            ExpressionAttributeValues={
                ':db_uuid': {'S': db_uuid}
            }
        )
        dynamodb.update_item(
            TableName=table_name,
            Key={
                'id': {'S': internal_ica_event.detail.portalRunId},
                'id_type': {'S': 'portal_run_id'}
            },
            UpdateExpression='SET db_uuid = :db_uuid',
            ExpressionAttributeValues={
                ':db_uuid': {'S': db_uuid}
            }
        )
        logger.info(f"db_uuid updated in anaylsis_id and portal_run_id record.")
    except Exception as e:
        raise Exception("Failed to store event in the DynamoDB table. Error: ", e)

    return {
        "statusCode": 200,
        "body": json.dumps("Internal event sent to the event bus and both msg stored in the DynamoDB table.")
    }


# Convert from Entity model to aws event object with aws event envelope
def translate_to_aws_event(event) -> AWSEvent:
    return AWSEvent(
        detail=get_event_details(event),
        detail_type="WorkflowRunStateChange",
        source="orcabus.bclconvertmanager",
        # version="0.1.0",  # comment as the version is managed by the event bus
    )


# Convert from entity module to internal event details
def get_event_details(event) -> WorkflowRunStateChange:
    # Extract relevant fields from the event payload
    project_id = event.get("projectId", '')
    analysis_status = event.get("eventParameters", {}).get("analysisStatus", '')

    payload = event.get("payload", {})
    analysis_id = payload.get("id", '')
    pipeline = payload.get("pipeline", {})

    analysis_outputs = collect_analysis_objects(
        project_id, analysis_id
    )

    # generate internal event with required attributes
    return WorkflowRunStateChange(
        portal_run_id=get_portal_run_id(payload.get("id", '')),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        status=analysis_status,
        workflow_type="bclconvert_manager",
        workflow_version="4.2.7",
        payload={
            "refId": None,
            "version": "0.1.0",
            "data": {
                "projectId": project_id,
                "analysisId": analysis_id,
                "userReference": payload.get("userReference", ''),
                "timeCreated": payload.get("timeCreated", ""),
                "timeModified": payload.get("timeModified", ""),
                "pipelineId": pipeline.get("id", ''),
                "pipelineCode": pipeline.get("code", ''),
                "pipelineDescription": pipeline.get("description", ''),
                "pipelineUrn": pipeline.get("urn", ''),
                "instrumentRunId": analysis_outputs.get("instrument_run_id"),
                "basespaceRunId": analysis_outputs.get("basespace_run_id"),
                "samplesheetB64gz": analysis_outputs.get("samplesheet_b64gz")
            }
        }
    )


# check the dynamodb table to see if new portal run id is required
def get_portal_run_id(analysis_id: str) -> str:
    # check if dynomodb table have the anylsis id
    table_name = os.getenv("TABLE_NAME")
    try:
        response = get_dynamodb_client().query(
            TableName=table_name,
            KeyConditionExpression='id = :analysis_id and id_type = :id_type',
            ExpressionAttributeValues={
                ':analysis_id': {'S': analysis_id},
                ':id_type': {'S': 'analysis_id'}
            }
        )
        items = response.get('Items', [])

        # check if the response.Items has items
        # if exist return the portal run id
        # if not create new portal run and store run id in the dynamodb table
        if items:
            logger.info(f"Analysis id already exists in the DynamoDB table.")
            return items[0].get("portal_run_id").get("S")
        else:
            return generate_new_portal_run(analysis_id)

    except Exception as e:
        raise Exception("Failed to get item from the DynamoDB table. Error: ", e)


# create new portal run and store run id in the dynamodb table
def generate_new_portal_run(analysis_id: str) -> str:
    table_name = os.getenv("TABLE_NAME")
    new_portal_run_id = generate_portal_run_id()
    # put analysis_id <=> portal_run_id map record in the dynamodb table
    try:
        get_dynamodb_client().put_item(
            TableName=table_name,
            Item={
                'id': {'S': analysis_id},
                'id_type': {'S': 'analysis_id'},
                "portal_run_id": {'S': new_portal_run_id}
            }
        )
        get_dynamodb_client().put_item(
            TableName=table_name,
            Item={
                'id': {'S': new_portal_run_id},
                'id_type': {'S': 'portal_run_id'},
                "analysis_id": {'S': analysis_id}
            }
        )
    except Exception as e:
        raise Exception("Failed to store new portal run id in the DynamoDB table. Error: ", e)
    logger.info(f"New portal run id created and stored in the DynamoDB table.")
    return new_portal_run_id


def generate_portal_run_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d')}{str(uuid4())[:8]}"


def generate_db_uuid() -> str:
    # UUID7 database returns a time-sampled UUID
    return str(uuid7())