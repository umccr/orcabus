import os
import logging
import json
from libumccr.aws import libeb
import workflow_manager.aws_event_bridge.workflowmanager.workflowrunstatechange as wfm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def emit_wrsc_api_event(event):
    """
    Emit events to the event bridge sourced from the workflow manager API
    """
    source = "orcabus.workflowmanagerapi"
    event_bus_name = os.environ.get("EVENT_BUS_NAME", None)

    if event_bus_name is None:
        raise ValueError("EVENT_BUS_NAME environment variable is not set.")

    logger.info(f"Emitting event: {event}")
    response = libeb.emit_event({
        'Source': source,
        'DetailType': wfm.WorkflowRunStateChange.__name__,
        'Detail': json.dumps(wfm.Marshaller.marshall(event)),
        'EventBusName': event_bus_name,
    })

    logger.info(f"Sent a WRSC event to event bus {event_bus_name}:")
    logger.info(event)
    logger.info(f"{__name__} done.")
    return response
