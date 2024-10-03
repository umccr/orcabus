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
(Non-SUCCEEDED Event without payload)
{
    "portalRunId": '20xxxxxxxxxx',
    "executionId": "valid_payload_id",
    "timestamp": "2024-00-25T00:07:00Z",
    "status": "FAILED", (Non-SUCCEEDED status)
    "workflowName": "BclConvert",
    "workflowVersion": "4.2.7",
    workflowRunName: "123456_A1234_0000_TestingPattern",
}

(SUCCEEDED Event)
{
    "portalRunId": '20xxxxxxxxxx',
    "executionId": "valid_payload_id",
    "timestamp": "2024-00-25T00:07:00Z",
    "status": "SUCCEEDED",
    "workflowName": "BclConvert",
    "workflowVersion": "4.2.7",
    workflowRunName: "123456_A1234_0000_TestingPattern",
    "payload": {
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
            "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0"
            "instrumentRunId": "12345_A12345_1234_ABCDE12345",
            "basespaceRunId": "1234567",
            "samplesheetB64gz": "H4sIAFGBVWYC/9VaUW+jOBD+Kyvu9VqBgST0njhWh046..."
        }
    }
}
"""
import os
import json
import logging
import datetime
import boto3
from helper.workflowrunstatechange import (
    WorkflowRunStateChange,
    AWSEvent,
    Marshaller as WorkflowRunStateChangeMarshaller,
)
from helper.payloaddatasucceeded import (
    PayloadDataSucceeded,
    Marshaller as PayloadDataMarshaller,
)
from helper.icav2_analysis import collect_analysis_objects
from helper.aws_ssm_helper import set_icav2_env_vars
from helper.generate_db_uuid import generate_db_uuid
from helper.generate_portal_run_id import generate_portal_run_id

events = boto3.client("events", region_name='ap-southeast-2')
dynamodb = boto3.client('dynamodb', region_name='ap-southeast-2')

# Set loggers
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    assert os.getenv("EVENT_BUS_NAME"), "EVENT_BUS_NAME environment variable is not set"
    assert os.getenv("TABLE_NAME"), "TABLE_NAME environment variable is not set"
    assert os.getenv("ICAV2_BASE_URL"), "ICAV2_BASE_URL environment variable is not set"
    assert os.getenv("ICAV2_ACCESS_TOKEN_SECRET_ID"), "ICAV2_ACCESS_TOKEN_SECRET_ID environment variable is not set"

    event_bus_name = os.getenv("EVENT_BUS_NAME")
    table_name = os.getenv("TABLE_NAME")

    # Set ICAv2 env variables
    logger.info("Setting icav2 env vars from secrets manager")
    set_icav2_env_vars()

    # Extract relevant fields from the event payload
    event_details = event.get("detail", {}).get("ica-event", {})

    # Generate internal AWS event (orcabus.wfm@WorkflowRunStateChange)
    internal_ica_event = translate_to_aws_event(event_details)

    # send the internal event to the event bus
    send_internal_event_to_eventbus(internal_ica_event, event_bus_name)

    # Store the internal event in the DynamoDB table
    store_events_into_dynamodb(internal_ica_event, table_name, event_details)

    return {
        "statusCode": 200,
        "body": json.dumps("Internal event sent to the event bus and both msg stored in the DynamoDB table.")
    }


# send the internal event to the event bus
def send_internal_event_to_eventbus(internal_ica_event, event_bus_name) -> None:
    try:
        events.put_events(
            Entries=[
                {
                    "Source": internal_ica_event.source,
                    "DetailType": internal_ica_event.detail_type,
                    "Detail": json.dumps(WorkflowRunStateChangeMarshaller.marshall(internal_ica_event.detail)),
                    "EventBusName": event_bus_name
                }
            ]
        )
        logger.info(f"Internal event sent to the event bus.")
    except Exception as e:
        raise Exception("Failed to send event to the event bus. Error: ", e)


# Store the internal event in the DynamoDB table
def store_events_into_dynamodb(internal_ica_event, table_name, event_details) -> None:
    try:
        db_uuid = generate_db_uuid().get("db_uuid",'')
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'id': {'S': db_uuid},
                'id_type': {'S': 'db_uuid'},
                'analysis_id': {'S': event_details.get("payload", {}).get("id", '')},
                'analysis_status': {'S': internal_ica_event.detail.status}, # 'SUCCEEDED', 'FAILED', 'ABORTED'
                "portal_run_id": {'S': internal_ica_event.detail.portalRunId},
                'original_external_event': {'S': json.dumps(event_details)},
                'translated_internal_ica_event': {'S': json.dumps(WorkflowRunStateChangeMarshaller.marshall(internal_ica_event.detail))},
                'timestamp': {'S': internal_ica_event.detail.timestamp}
            }
        )
        logger.info(f"Original and Internal events stored in the DynamoDB table.")

        # update dynamodb table with the new generate db_uuid
        dynamodb.update_item(
            TableName=table_name,
            Key={
                'id': {'S': event_details.get("payload", {}).get("id", '')},
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


# Convert from Entity model to aws event object with aws event envelope
def translate_to_aws_event(event) -> AWSEvent:
    return AWSEvent(
        detail=get_event_details(event),
        detail_type="WorkflowRunStateChange",
        source="orcabus.bclconvertmanager",
        # version="0.1.0",  # comment as the version is managed by the evnet bus
    )


# Convert from entity module to internal event details
def get_event_details(event) -> WorkflowRunStateChange:
    # Extract relevant fields from the event payload
    analysis_status = event.get("eventParameters", {}).get("analysisStatus", 'UNSPECIFIED')

    payload = event.get("payload", {})
    analysis_id = payload.get("id", '')
    pipeline = payload.get("pipeline", {})

    event_name, version = parse_event_code(pipeline.get("code", ''))
    
    if analysis_status != "SUCCEEDED":
        # generate internal event without payload
        return WorkflowRunStateChange(
            portalRunId=get_portal_run_id(analysis_id),
            executionId=analysis_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            status=analysis_status,
            workflowName=event_name,
            workflowVersion=version,
            workflowRunName=payload.get("userReference", ''),
        )

    succeeded_payload_data = get_succeeded_payload_data(event)

    # generate internal event with required attributes
    return WorkflowRunStateChange(
        portalRunId=get_portal_run_id(payload.get("id", '')),
        executionId=analysis_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        status=analysis_status,
        workflowName=event_name,
        workflowVersion=version,
        workflowRunName=payload.get("userReference", ''),
        payload={
            "version": "0.1.0",
            "data": PayloadDataMarshaller.marshall(succeeded_payload_data)
        }
    )

def get_succeeded_payload_data(event) -> PayloadDataSucceeded:
    # Extract relevant fields from the event payload
    project_id = event.get("projectId", '')

    payload = event.get("payload", {})
    analysis_id = payload.get("id", '')
    pipeline = payload.get("pipeline", {})
    
    analysis_outputs = collect_analysis_objects(
        project_id, analysis_id
    )
    
    return PayloadDataSucceeded(
        projectId=project_id,
        analysisId=analysis_id,
        userReference=payload.get("userReference", ''),
        timeCreated=payload.get("timeCreated", ""),
        timeModified=payload.get("timeModified", ""),
        pipelineId=pipeline.get("id", ''),
        pipelineCode=pipeline.get("code", ''),
        pipelineDescription=pipeline.get("description", ''),
        pipelineUrn=pipeline.get("urn", ''),
        instrumentRunId=analysis_outputs.get("instrument_run_id"),
        basespaceRunId=analysis_outputs.get("basespace_run_id"),
        samplesheetB64gz=analysis_outputs.get("samplesheet_b64gz")
    )
    

# check the dynamodb table to see if new portal run id is required
def get_portal_run_id(analysis_id: str) -> str:
    # check if dynomodb table have the anylsis id
    table_name = os.getenv("TABLE_NAME")
    try:
        response = dynamodb.query(
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
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'id': {'S': analysis_id},
                'id_type': {'S': 'analysis_id'},
                "portal_run_id": {'S': new_portal_run_id}
            }
        )
        dynamodb.put_item(
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


def parse_event_code(event_code):
    # Split the event code by space to separate the event name and version string
    parts = event_code.split(" ")
    if len(parts) != 2:
        raise ValueError("Event code format must be 'EventName vMajor_Minor_Patch'")

    event_name = parts[0]
    version_part = parts[1]

    # Remove the leading 'v' from the version string
    if not version_part.startswith('v'):
        raise ValueError("Version must start with 'v'")

    version_numbers = version_part[1:]  # Remove the 'v'

    # Split the version numbers by underscore
    version_numbers = version_numbers.split("_")
    if len(version_numbers) != 3:
        raise ValueError("Version must be in the format (Semantic Version) 'Major_Minor_Patch'")

    # Join the version numbers with dots to form the standard version format
    version = ".".join(version_numbers)

    return event_name, version


# if __name__ == "__main__":
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "version": "0",
#                     "id": "f15b5eb7-1bbd-030f-1a6c-fecbaccbfe6e",
#                     "detail-type": "Event from aws:sqs",
#                     "source": "Pipe IcaEventPipeConstru-aVEAl34nl7zf",
#                     "account": "843407916570",
#                     "time": "2024-05-28T03:54:20Z",
#                     "region": "ap-southeast-2",
#                     "resources": [],
#                     "detail": {
#                         "ica-event": {
#                             "correlationId": "94739e11-f3dc-486b-8a85-2d5a9e237b52",
#                             "timestamp": "2024-03-25T10:07:09.990Z",
#                             "eventCode": "ICA_EXEC_028",
#                             "eventParameters": {
#                                 "pipelineExecution": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
#                                 "analysisPreviousStatus": "INPROGRESS",
#                                 "analysisStatus": "SUCCEEDED"
#                             },
#                             "description": "Analysis status changed",
#                             "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22",
#                             "payloadVersion": "v3",
#                             "payload": {
#                                 "id": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
#                                 "timeCreated": "2024-03-25T08:04:40Z",
#                                 "timeModified": "2024-03-25T10:07:06Z",
#                                 "ownerId": "a9938581-7bf5-35d2-b461-282f34794dd1",
#                                 "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
#                                 "tenantName": "umccr-prod",
#                                 "reference": "240229_A00130_0288_BH5HM2DSXC_844951_4ce192-BclConvert v4_2_7-247cebc9-bacb-40fd-a13c-513cf713e36b",
#                                 "userReference": "240229_A00130_0288_BH5HM2DSXC_844951_4ce192",
#                                 "pipeline": {
#                                     "id": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca",
#                                     "timeCreated": "2023-11-13T22:16:50Z",
#                                     "timeModified": "2023-11-16T22:08:46Z",
#                                     "ownerId": "88de7b1d-bd37-37e8-8d29-6213bd79e976",
#                                     "tenantId": "55cb0a54-efab-4584-85da-dc6a0197d4c4",
#                                     "tenantName": "ilmn-dragen",
#                                     "code": "BclConvert v4_2_7",
#                                     "urn": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7",
#                                     "description": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
#                                     "language": "NEXTFLOW",
#                                     "languageVersion": {
#                                         "id": "b1585d18-f88c-4ca0-8d47-34f6c01eb6f3",
#                                         "name": "22.04.3",
#                                         "language": "NEXTFLOW"
#                                     },
#                                     "pipelineTags": {
#                                         "technicalTags": []
#                                     },
#                                     "analysisStorage": {
#                                         "id": "8bc4695d-5b20-43a8-aea3-181b4bf6f07e",
#                                         "timeCreated": "2023-02-16T21:36:11Z",
#                                         "timeModified": "2023-05-31T16:38:09Z",
#                                         "ownerId": "dda792d4-7e9c-3c5c-8d0b-93f0cdddd701",
#                                         "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
#                                         "tenantName": "ica-cp-admin",
#                                         "name": "XLarge",
#                                         "description": "16TB"
#                                     },
#                                     "proprietary": False
#                                 },
#                                 "workflowSession": {
#                                     "id": "89323106-f36c-433a-ba3b-00682a89f84b",
#                                     "timeCreated": "2024-03-25T07:57:35Z",
#                                     "ownerId": "a9938581-7bf5-35d2-b461-282f34794dd1",
#                                     "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
#                                     "tenantName": "umccr-prod",
#                                     "userReference": "ws_240229_A00130_0288_BH5HM2DSXC_844951",
#                                     "workflow": {
#                                         "id": "d691d76a-3a98-4669-ae09-088fb4c4b47d",
#                                         "code": "ica_workflow_1_2-23",
#                                         "urn": "urn:ilmn:ica:workflow:d691d76a-3a98-4669-ae09-088fb4c4b47d#ica_workflow_1_2-23",
#                                         "description": "ICA Workflow v2.23.0",
#                                         "languageVersion": {
#                                             "id": "2483549a-1530-4973-bb00-f3f6ccb7e610",
#                                             "name": "20.10.0",
#                                             "language": "NEXTFLOW"
#                                         },
#                                         "workflowTags": {
#                                             "technicalTags": []
#                                         },
#                                         "analysisStorage": {
#                                             "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
#                                             "timeCreated": "2021-11-05T10:28:20Z",
#                                             "timeModified": "2023-05-31T16:38:26Z",
#                                             "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
#                                             "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
#                                             "tenantName": "ica-cp-admin",
#                                             "name": "Small",
#                                             "description": "1.2TB"
#                                         }
#                                     },
#                                     "status": "INPROGRESS",
#                                     "startDate": "2024-03-25T07:57:48Z",
#                                     "summary": "",
#                                     "tags": {
#                                         "technicalTags": [
#                                             "/ilmn-runs/bssh_aps2-sh-prod_3882885/",
#                                             "240229_A00130_0288_BH5HM2DSXC",
#                                             "844951f7-6d66-449d-9212-495009437e3c"
#                                         ],
#                                         "userTags": [
#                                             "/ilmn-runs/bssh_aps2-sh-prod_3882885/"
#                                         ]
#                                     }
#                                 },
#                                 "status": "SUCCEEDED",
#                                 "startDate": "2024-03-25T08:04:51Z",
#                                 "endDate": "2024-03-25T10:07:05Z",
#                                 "summary": "",
#                                 "analysisStorage": {
#                                     "id": "3fab13dd-46e7-4b54-bb34-b80a01a99379",
#                                     "timeCreated": "2021-11-05T10:28:20Z",
#                                     "timeModified": "2023-05-31T16:38:14Z",
#                                     "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
#                                     "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
#                                     "tenantName": "ica-cp-admin",
#                                     "name": "Large",
#                                     "description": "7.2TB"
#                                 },
#                                 "analysisPriority": "MEDIUM",
#                                 "tags": {
#                                     "technicalTags": [
#                                         "RUN_ID",
#                                         "RUN_NAME",
#                                         "UNIQUE_ID"
#                                     ],
#                                     "userTags": [],
#                                     "referenceTags": []
#                                 }
#                             }
#                         }
#                     }
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "statusCode": 200,
#     #   "body": "\"Internal event sent to the event bus and both msg stored in the DynamoDB table.\""
#     # }


