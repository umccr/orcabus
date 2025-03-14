#!/usr/bin/env python3

""""
SFN LAMBDA HANDLER: __generate_presigned_url_for_data_objects_lambda_function_arn__

Intro:

Generate a presigned url for a data object using the ICAv2 API

# FIXME - use the filemanager once available
"""

# Imports
import typing
from os import environ
import boto3
from urllib.parse import urlunparse
from typing import Dict

# Wrapica imports
from wrapica.project_data import (
    convert_uri_to_project_data_obj,
    create_download_url
)

# Set mypy type hinting
if typing.TYPE_CHECKING:
    from filemanager_tools import FileObject
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from s3_json_tools import FileObjectWithMetadataAndPresignedUrlTypeDef


# Set logging
import logging
logger = logging.getLogger()
logger.setLevel("INFO")

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

# Set loggers
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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


def get_s3_uri_from_s3_file_object(s3_file_object: 'FileObject') -> str:
    return str(urlunparse(
        (
            "s3",
            s3_file_object['bucket'],
            s3_file_object['key'],
            None, None, None
        )
    ))


def handler(event, context) -> Dict[str, 'FileObjectWithMetadataAndPresignedUrlTypeDef']:
    """
    Get the presigned url for data objects
    :param event:
    :param context:
    :return:
    """

    # Set the icav2 env vars
    set_icav2_env_vars()

    # Get the input
    s3_file_object: 'FileObject' = event.get("s3FileObject", None)

    # Check if s3_uri is None
    if s3_file_object is None:
        raise ValueError("s3FileObject input parameter is required")

    # Get the project data object
    project_data_obj = convert_uri_to_project_data_obj(get_s3_uri_from_s3_file_object(s3_file_object))

    # Generate presigned url from project data object
    presigned_url = create_download_url(
        project_data_obj.project_id,
        project_data_obj.data.id
    )

    # Extend the s3 file object to contain the presigned Url
    s3_file_object_with_presigned_url: 'FileObjectWithMetadataAndPresignedUrlTypeDef' = s3_file_object.copy()
    s3_file_object_with_presigned_url['presignedUrl'] = presigned_url

    return {
        "s3FileObjectWithPresignedUrl": s3_file_object_with_presigned_url
    }
