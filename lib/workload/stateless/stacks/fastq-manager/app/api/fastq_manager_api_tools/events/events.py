#!/usr/bin/env python3
import json
import typing
from typing import Dict, List, Union
from os import environ

import boto3

from ..globals import (
    EVENT_BUS_NAME_ENV_VAR,
    EVENT_SOURCE_ENV_VAR,
    FastqListRowEventDetailTypeEnum,
    FastqSetEventDetailTypeEnum
)
from ..models.fastq_list_row import FastqListRowResponse
from ..models.fastq_set import FastqSetResponse

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
def put_fastq_list_row_create_event(fastq_list_row_response_object: FastqListRowResponse):
    """
    Put a create event to the event bus.
    """
    put_event(FastqListRowEventDetailTypeEnum.CREATE.value, fastq_list_row_response_object)


def put_fastq_set_create_event(fastq_set_create_event: FastqSetResponse):
    """
    Put a create event to the event bus.
    """
    put_event(FastqSetEventDetailTypeEnum.CREATE.value, fastq_set_create_event)


# Update events
def put_fastq_list_row_update_event(fastq_list_row_response_object: FastqListRowResponse):
    """
    Put a update event to the event bus.
    """
    put_event(FastqListRowEventDetailTypeEnum.UPDATE.value, fastq_list_row_response_object)


def put_fastq_set_update_event(fastq_set_update_event: FastqSetResponse):
    """
    Put a update event to the event bus.
    """
    put_event(FastqSetEventDetailTypeEnum.UPDATE.value, fastq_set_update_event)


def put_fastq_set_merge_event(fastq_set_merge_event: Dict[str, Union[str, List[str], Dict[str, str]]]):
    """
    Put a update event to the event bus.
    """
    put_event(FastqSetEventDetailTypeEnum.MERGE.value, fastq_set_merge_event)


# Delete events
def put_fastq_list_row_delete_event(fastq_list_row_id: str):
    """
    Put a delete event to the event bus.
    """
    put_event(FastqListRowEventDetailTypeEnum.DELETE.value, {"fastqListRowId": fastq_list_row_id})


def put_fastq_set_delete_event(fastq_set_id: str):
    """
    Put a update event to the event bus.
    """
    put_event(FastqSetEventDetailTypeEnum.DELETE.value, {"fastqSetId": fastq_set_id})
