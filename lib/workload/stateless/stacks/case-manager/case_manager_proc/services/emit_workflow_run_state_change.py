import os
import boto3
import json
import case_manager_proc.domain.casemanager.caserunstatechange as case
from case_manager_proc.domain.casemanager.caserunstatechange import CaseRunStateChange
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = boto3.client('events')
source = "orcabus.casemanager"
event_bus_name = os.environ["EVENT_BUS_NAME"]


def handler(event, context):
    """
    event has to be JSON conform to casemanager.CaseRunStateChange
    """
    logger.info(f"Processing {event}, {context}")

    response = client.put_events(
        Entries=[
            {
                'Source': source,
                'DetailType': CaseRunStateChange.__name__,
                'Detail': json.dumps(case.Marshaller.marshall(event)),
                'EventBusName': event_bus_name,
            },
        ],
    )

    logger.info(f"Sent a WRSC event to event bus {event_bus_name}:")
    logger.info(event)
    logger.info(f"{__name__} done.")
    return response
