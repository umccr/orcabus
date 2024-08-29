#!/usr/bin/env python3

"""
Given an s3 output uri perform the following functions

1. Convert the s3 uri into an icav2 uri
2. If the icav2 uri is of a folder type, set class to Directory
3. If the icav2 uri is of a file type, set class to File
4. Use the uri as the location attribute
5. Provide the basename as the basename attribute
"""

# AWS improts
import boto3
from os import environ
import typing

# Wrapica imports
from wrapica.project_data import (
    convert_uri_to_project_data_obj,
    convert_project_data_obj_to_uri
)
from wrapica.enums import UriType, DataType
from wrapica.libica_models import ProjectData

# Type hints
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_secret(secret_id: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_id)["SecretString"]


# Functions
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def handler(event, context):
    """
    Expect an s3 uri as the input from the key 's3_uri'
    :param event:
    :param context:
    :return:
    """

    # Set env vars
    set_icav2_env_vars()

    # Get the s3 uri
    s3_uri = event['s3_uri']

    # Convert to a project data object
    s3_uri_project_data_obj: ProjectData = convert_uri_to_project_data_obj(s3_uri)

    # Return the project data object as an icav2 cwl directory
    return {
        "cwl_object": {
            "basename": s3_uri_project_data_obj.data.details.name,
            "class": (
                "Directory"
                if DataType(s3_uri_project_data_obj.data.details.data_type) == DataType.FOLDER
                else "File"
            ),
            "location": convert_project_data_obj_to_uri(
                s3_uri_project_data_obj,
                uri_type=UriType.ICAV2
            )
        }
    }
