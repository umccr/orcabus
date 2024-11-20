import os
import logging
import boto3
import json
from typing import Literal
import workflow_manager.aws_event_bridge.workflowmanager.workflowrunstatechange as wfm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = boto3.client('events')
event_bus_name = os.environ["EVENT_BUS_NAME"]


def emit_wrsc_api_event(event):
    """
    Emit events to the event bridge sourced from the workflow manager API
    """
    source = "orcabus.workflowmanager"

    logger.info(f"Emitting event: {event}")

    response = client.put_events(
        Entries=[
            {
                'Source': source,
                'DetailType': wfm.WorkflowRunStateChange.__name__,
                'Detail': json.dumps(wfm.Marshaller.marshall(event)),
                'EventBusName': event_bus_name,
            },
        ],
    )

    logger.info(f"Sent a WRSC event to event bus {event_bus_name}:")
    logger.info(event)
    logger.info(f"{__name__} done.")
    return response
