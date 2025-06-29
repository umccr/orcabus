#!/usr/bin/env python3

"""
Given the following

* libraryOrcabusId

Get the library object, and return the projectId

* projectId
"""

import boto3
import typing

from metadata_tools import get_library_from_library_orcabus_id

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """

    # Inputs
    library_orcabus_id = event.get("libraryOrcabusId")

    # Get the library object
    library_obj = get_library_from_library_orcabus_id(library_orcabus_id)

    # Return the projectId
    return {
        "projectId": library_obj['projectSet'][0]['projectId']
    }