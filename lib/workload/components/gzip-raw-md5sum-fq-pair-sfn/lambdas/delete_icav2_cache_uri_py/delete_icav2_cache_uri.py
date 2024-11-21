#!/usr/bin/env python3

"""
Delete the ICAv2 URI Cache folder

This script will delete the ICAv2 URI Cache folder.
This folder is used to write out the md5sum files for each of the read pairs
Now that we have the files, this folder is no longer needed.
"""
import boto3
from os import environ
import typing

# Wrapica imports
from wrapica.enums import DataType
from wrapica.project_data import (
    convert_uri_to_project_data_obj, list_project_data_non_recursively, delete_project_data
)
import logging
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

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


def handler(event, context):
    """
    Import
    Args:
        event:
        context:

    Returns:

    """
    set_icav2_env_vars()

    # Part 0 - get inputs
    cache_uri = event.get("cache_uri", None)

    # Check cache uri
    if cache_uri is None:
        raise ValueError("No cache_uri provided")

    # Part 1 - check that in the cache uri, that only the following files exist:
    # 1. R1.md5sum.txt
    # 2. R2.md5sum.txt
    try:
        cache_obj = convert_uri_to_project_data_obj(cache_uri)
    except NotADirectoryError as e:
        logger.info("Cache directory has already been deleted")
        return None

    cache_folder_list = list_project_data_non_recursively(
        project_id=cache_obj.project_id,
        parent_folder_id=cache_obj.data.id,
    )

    try:
        not_md5sum_file = next(
            filter(
                lambda project_data_obj_iter: (
                        (not project_data_obj_iter.data.details.name in [ "R1.md5sum.txt", "R2.md5sum.txt" ]) or
                        (not DataType[project_data_obj_iter.data.details.data_type] == DataType.FILE)
                ),
                cache_folder_list
            )
        )
    except StopIteration:
        # We expect to get here, we do not expect any non-fastq files in the sample folder
        pass
    else:
        raise ValueError(
            f"Non md5sum file in the cache directory"
        )

    # Check that the directory has two entries overall
    if not len(cache_folder_list) == 2:
        raise ValueError(
            f"Expected two entries in the cache folder list, R1.md5sum.txt and R2.md5sum.txt "
            f"but got {len(cache_folder_list)}: "
            f"{', '.join([project_data_obj.data.details.name for project_data_obj in cache_folder_list])}"
        )

    # Delete the cache directory
    delete_project_data(
        project_id=cache_obj.project_id,
        data_id=cache_obj.data.id,
    )

# if __name__ == "__main__":
#     import json
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-trial"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "cache_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20240510abcd0026/L2301368_run_cache/"
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#     # null


