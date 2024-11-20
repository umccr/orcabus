#!/usr/bin/env python3

"""
Rerun the analysis with a new dataset

Given a portal run id, and a dataset regenerate the ready payload
and rerun the analysis.

Replace all instances of the portal run id with a new portal run id
"""

# Standard imports
from datetime import datetime, timezone
import random
from typing import Dict
from os import environ
import boto3
import json

# External imports
from workflow_tools.utils.payload_helpers import get_payload
from workflow_tools.utils.workflow_run_helpers import get_workflow_run_from_portal_run_id, get_workflow_run_state

# Globals
ORCABUS_TOKEN = None


# Functions
def get_event_bridge_session():
    """
    Get the event bridge session
    :return:
    """
    return boto3.Session().client("events")


def generate_portal_run_id():
    """
    Return a new portal run id in the format
    YYYYMMDD{8-digit-random-hexadecimal}
    :return:
    """
    return datetime.now(timezone.utc).strftime("%Y%m%d") + "{:08x}".format(random.getrandbits(32))


def replace_portal_run_id(old_portal_run_id, new_portal_run_id, payload: Dict) -> Dict:
    """
    Replace all instances of the old portal run id with the new portal run id
    :param old_portal_run_id: 
    :param new_portal_run_id: 
    :param payload: 
    :return: 
    """
    return json.loads(
        json.dumps(payload).replace(old_portal_run_id, new_portal_run_id)
    )


def get_utc_timestamp() -> str:
    """
    Get a UTC timestamp in ISO format
    :return:
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def remove_ref_id_from_payload(payload: Dict) -> Dict:
    """
    Remove the ref_id from the payload
    :param payload:
    :return:
    """
    payload.pop("payloadRefId", None)
    payload.pop("orcabusId", None)
    return payload


def update_dataset(payload: Dict, new_dataset: str) -> Dict:
    """
    Update the dataset in the payload
    :param payload:
    :return:
    """
    payload["data"]["inputs"]["dataset"] = new_dataset
    return payload


def handler(event, context):
    """
    Given a portal run id and a dataset, regenerate the ready payload
    :param event:
    :param context:
    :return:
    """

    # Get the old portal run id
    old_portal_run_id = event["portal_run_id"]

    # Get the new dataset
    new_dataset = event["dataset"]

    # Get the workflow object from the old portal run id
    workflow_obj = get_workflow_run_from_portal_run_id(old_portal_run_id)
    # Get the READY run state
    workflow_ready_run_state_obj = get_workflow_run_state(workflow_obj.get("orcabusId"), "READY")
    # Get the payload from the READY run state
    payload_obj = get_payload(workflow_ready_run_state_obj.get("payload"))

    # Generate a new portal run id
    new_portal_run_id = generate_portal_run_id()

    # Replace the old portal run id with the new portal run id
    new_payload = replace_portal_run_id(old_portal_run_id, new_portal_run_id, payload_obj)
    # Remove the refId from the previous payload
    new_payload = remove_ref_id_from_payload(new_payload)
    # Update the dataset in the payload
    new_payload = update_dataset(new_payload, new_dataset)

    # Regenerate the event detail
    detail_dict: Dict = {
        "portalRunId": new_portal_run_id,
        "timestamp": get_utc_timestamp(),
        "status": "READY",
        "workflowName": workflow_obj.get("workflow").get("workflowName"),
        "workflowVersion": workflow_obj.get("workflow").get("workflowVersion"),
        "workflowRunName": workflow_obj.get("workflowRunName").replace(old_portal_run_id, new_portal_run_id),
        "linkedLibraries": workflow_obj.get("libraries"),
        "payload": new_payload
    }

    # Put the event to the event bus
    return get_event_bridge_session().put_events(
        Entries=[
            {
                "EventBusName": environ["EVENT_BUS_NAME"],
                "Source": "orcabus.manual",
                "DetailType": "WorkflowRunStateChange",
                "Detail": json.dumps(detail_dict),
            }
        ]
    )['Entries']


# if __name__ == "__main__":
#     # Import the json module
#     import json
#
#     # Set the environment variables
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['EVENT_BUS_NAME'] = 'OrcaBusMain'
#
#     print(
#         json.dumps(
#             handler(
#             {
#                     "portal_run_id": "2024111144ce2633",
#                     "dataset": "GBM"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # [
#     #   {
#     #     "EventId": "c916b0c7-7476-c96e-1acf-c7caf0eed639"
#     #   }
#     # ]
