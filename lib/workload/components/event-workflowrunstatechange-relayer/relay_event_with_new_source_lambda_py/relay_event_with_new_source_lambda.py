#!/usr/bin/env python

"""
Simply update the status of a workflow run statechange event and push back to the event bus

This takes a succeeded status from a non-workflow-manage service, and duplicates that event from the workflowrunmanager
source with a 'complete' status.

Pushes an event based on the putSource event attribute,

ALl other attributes remain the same
"""

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
    new_event = translate_to_aws_event_with_new_source(event)

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
    # generate internal event with required attributes
    return WorkflowRunStateChange(
        portal_run_id=handle_portal_run_id(event),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        status=environ["OUTPUT_EVENT_STATUS"],  # change the status to complete from succeeded
        workflow_name=event.get("workflowName"),
        workflow_version=event.get("workflowVersion"),
        payload=event.get("payload")
    )


def handle_portal_run_id(event):
    # If the portal run id is in the event, then we relay this
    if "portalRunId" in event:
        return event.get("portalRunId")

    # If the portal run id is not in the event and we need one (because this is a 'ready' event)
    # Then we need to generate one
    if environ["OUTPUT_EVENT_STATUS"] == "ready":
        return generate_portal_run_id()
