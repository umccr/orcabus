import os
import boto3
import json
import workflow_manager.aws_event_bridge.workflowmanager.workflowrunstatechange as wfm
from workflow_manager.aws_event_bridge.workflowmanager.workflowrunstatechange import WorkflowRunStateChange
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = boto3.client('events')
source = "orcabus.workflowmanager"
event_bus_name = os.environ["EVENT_BUS_NAME"]


def handler(event, context):
    """
    event has to be JSON conform to workflowmanager.WorkflowRunStateChange
    """
    logger.info(f"Processing {event}, {context}")

    response = client.put_events(
        Entries=[
            {
                'Source': source,
                'DetailType': WorkflowRunStateChange.__name__,
                'Detail': json.dumps(wfm.Marshaller.marshall(event)),
                'EventBusName': event_bus_name,
            },
        ],
    )

    logger.info(f"Sent a WRSC event to event bus {event_bus_name}:")
    logger.info(event)
    logger.info(f"{__name__} done.")
    return response
