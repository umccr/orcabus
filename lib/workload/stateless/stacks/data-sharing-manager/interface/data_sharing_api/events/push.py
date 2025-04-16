#!/usr/bin/env python3

"""
Generate datasharing push events to push to the server
"""

from ..globals import PushEventDetailTypeEnum
from ..models.push import PushJobResponse
from . import put_event


# CREATE events
def put_push_job_create_event(push_response_object: PushJobResponse):
    """
    Put a create event to the event bus.
    """
    put_event(PushEventDetailTypeEnum.CREATE.value, push_response_object)


# Update events
def put_push_job_update_event(push_response_object: PushJobResponse):
    """
    Put a update event to the event bus.
    """
    put_event(PushEventDetailTypeEnum.UPDATE.value, push_response_object)
