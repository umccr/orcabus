#!/usr/bin/env python3

from ..globals import PackageEventDetailTypeEnum
from ..models.package import PackageResponseDict
from . import put_event


# CREATE events
def put_package_create_event(package_response_object: PackageResponseDict):
    """
    Put a create event to the event bus.
    """
    put_event(PackageEventDetailTypeEnum.CREATE.value, package_response_object)


# Update events
def put_package_update_event(package_response_object: PackageResponseDict):
    """
    Put a update event to the event bus.
    """
    put_event(PackageEventDetailTypeEnum.UPDATE.value, package_response_object)
