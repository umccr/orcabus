#!/usr/bin/env python3
import json
import typing
from typing import Dict, List, Union
from os import environ

import boto3

from ..globals import (
    EVENT_BUS_NAME_ENV_VAR,
    EVENT_SOURCE_ENV_VAR,
    JobEventDetailTypeEnum
)
from ..models.job import JobResponse

if typing.TYPE_CHECKING:
    from mypy_boto3_events import EventBridgeClient


def get_event_client() -> 'EventBridgeClient':
    """
    Get the event client for AWS EventBridge.
    """
    return boto3.client('events')


def put_event(event_detail_type, event_detail):
    # DEBUG
    if environ.get(EVENT_BUS_NAME_ENV_VAR) == 'local':
        return
    get_event_client().put_events(
        Entries=[
            {
                'EventBusName': environ[EVENT_BUS_NAME_ENV_VAR],
                'Source': environ[EVENT_SOURCE_ENV_VAR],
                'DetailType': event_detail_type,
                'Detail': json.dumps(event_detail),
            },
        ]
    )


# CREATE events
def put_job_create_event(job_response_object: JobResponse):
    """
    Put a create event to the event bus.
    """
    put_event(JobEventDetailTypeEnum.CREATE.value, job_response_object)


# Update events
def put_job_update_event(job_response_object: JobResponse):
    """
    Put a update event to the event bus.
    """
    put_event(JobEventDetailTypeEnum.UPDATE.value, job_response_object)
