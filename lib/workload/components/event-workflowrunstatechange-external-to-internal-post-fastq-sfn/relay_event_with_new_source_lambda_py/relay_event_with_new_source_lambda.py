#!/usr/bin/env python

"""
Simply update the status of a workflow run statechange event and push back to the event bus

This takes a succeeded status from a non-workflow-manage service, and duplicates that event from the workflowrunmanager
source with a 'complete' status.

Pushes an event based on the putSource event attribute,

ALl other attributes remain the same
"""
from copy import deepcopy

from workflowrunstatechange import WorkflowRunStateChange, AWSEvent, Marshaller, generate_portal_run_id
from datetime import datetime, timezone
from os import environ
import boto3
import json
import typing
import logging


if typing.TYPE_CHECKING:
    from mypy_boto3_events.client import EventBridgeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def get_events_client() -> 'EventBridgeClient':
    return boto3.client('events')


def handler(event, context):
    # FIXME - I don't think we know full construct use-case just yet
    # FIXME - if anything this should be its own construct called 'translate event detail'
    # Update refid
    event['event_input']['detail']['payload']['refId'] = event["reference_id"]

    if (
            event['event_input_type'] == 'workflowCompleteExternal' and
            event['event_output_type'] == 'workflowCompleteInternal'
    ):
        new_event = translate_to_aws_event_with_new_source(event['event_input'])
        return json.dumps(Marshaller.marshall(new_event.detail))
    elif (
        event['event_input_type'] == 'inputMaker' and
        event['event_output_type'] == 'ready'
    ):
        # Override portal run id in the event payload
        if 'portal_run_id' in event.keys() and 'event_input' in event.keys():
            event['event_input']['portalRunId'] = event['portal_run_id']
        new_event = translate_to_aws_event_with_new_source(event['event_input'])
        return json.dumps(Marshaller.marshall(new_event.detail))
    else:
        new_event = translate_to_aws_event_with_new_source(event['event_input'])
        try:
            get_events_client().put_events(
                Entries=[
                    {
                        "Source": new_event.source,
                        "DetailType": new_event.detail_type,
                        "Detail": json.dumps(Marshaller.marshall(new_event.detail)),
                        "EventBusName": environ["EVENT_BUS_NAME"]
                    }
                ]
            )
            logger.info(f"Internal event sent to the event bus.")
        except Exception as e:
            raise Exception("Failed to send event to the event bus. Error: ", e)


def translate_to_aws_event_with_new_source(event) -> AWSEvent:
    return AWSEvent(
        detail=get_event_details(event),
        detail_type=environ["OUTPUT_EVENT_DETAIL_TYPE"],
        source=environ["OUTPUT_EVENT_SOURCE"],
    )


def get_event_details(event) -> WorkflowRunStateChange:
    # Generate portal run id
    new_portal_run_id = generate_portal_run_id()
    # generate internal event with required attributes
    return WorkflowRunStateChange(
        portal_run_id=handle_portal_run_id(event, new_portal_run_id),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        status=environ["OUTPUT_EVENT_STATUS"],  # change the status to complete from succeeded
        workflow_name=event.get("workflowName"),
        workflow_version=event.get("workflowVersion"),
        payload=handle_payload(event.get("payload"), new_portal_run_id),
    )


def handle_portal_run_id(event, portal_run_id):
    # If the portal run id is in the event, then we relay this
    if "portalRunId" in event:
        return event.get("portalRunId")

    # If the portal run id is not in the event and we need one (because this is a 'ready' event)
    # Then we need to generate one
    if environ["OUTPUT_EVENT_STATUS"] == "ready":
        return portal_run_id


def handle_payload(payload: typing.Dict, portal_run_id: str):
    # Recursively traverse the payload data attribute, replace values
    # where __portal_run_id__ is found with portal_run_id
    payload = deepcopy(payload)
    for key, item in deepcopy(payload).items():
        if isinstance(item, dict):
            payload[key] = handle_payload(item, portal_run_id)
        elif isinstance(item, list):
            for i in deepcopy(payload[key]):
                payload[key][i] = handle_payload(i, portal_run_id)
        elif isinstance(item, str):
            payload[key] = item.replace("__portalRunId__", portal_run_id)

    return payload
