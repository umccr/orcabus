#!/usr/bin/env python3

"""
Given a source uri list and a destination uri, deconstruct into the following.

{
  "sourceList": [ {"prj.1234", "fil.123456"}, {"fil.1234567", "fol.123456" ],
  "destinationId": "folder.123456",
  "recursiveCopyJobsList": [
    {
      "destinationId": "fol.123567",
      "sourceIdList": ["fil.123456", "fil.123457", "fol.56789"]
    }
  ]
}

The source uri may be a file or a directory, the destination uri must be a directory.

If any item in the sourceIdList is a folder, we list the folder non-recursively and add the files in that folder to an
item in the recursiveCopyJobsList.

Due to AWS S3 Object tagging bugs, it's important each folder is part of its own job so we can handle single-part files correctly.

"""

# Standard imports
from typing import List, Dict, Union
import typing
from pathlib import Path
import logging
import boto3
from os import environ

# Wrapica imports
from wrapica.project_data import (
    coerce_data_id_or_uri_to_project_data_obj,
    ProjectData, list_project_data_non_recursively, create_folder_in_project
)

from wrapica.enums import DataType


# Set logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


# Type hints
if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient


# AWS things
def get_ssm_client() -> 'SSMClient':
    """
    Return SSM client
    """
    return boto3.client("ssm")


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_ssm_parameter_value(parameter_path) -> str:
    """
    Get the ssm parameter value from the parameter path
    :param parameter_path:
    :return:
    """
    return get_ssm_client().get_parameter(Name=parameter_path)["Parameter"]["Value"]


def get_secret(secret_arn: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_arn)["SecretString"]


# Set the icav2 environment variables
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def get_files_and_folders_in_project_folder_non_recursively(project_data_folder: ProjectData) -> List[ProjectData]:
    """
    Given a project data folder, return a list of all files in the folder
    """

    # Get the file list
    data_list = list_project_data_non_recursively(
        project_id=project_data_folder.project_id,
        parent_folder_id=project_data_folder.data.id,
    )

    # Return the list of files (and this one)
    return data_list


def sort_project_data_bulk_into_parent_folders(project_data_list: List[ProjectData]) -> Dict[str, List[str]]:
    """
    Given a list of project data, sort the files into parent folders and return a list of file ids for each folder
    """
    # Get all folders
    all_folders_list = list(filter(
        lambda project_data_iter_: DataType[project_data_iter_.data.details.dataType] == DataType.FOLDER,
        project_data_list
    ))

    # Get all files
    all_files_list = list(filter(
        lambda project_data_iter_: DataType[project_data_iter_.data.details.dataType] == DataType.FILE,
        project_data_list
    ))

    # Initialize the dictionary
    parent_folder_dict = {}

    # Iterate over the project data
    for project_file_data in all_files_list:

        # Get the parent folder id
        parent_folder_obj = next(filter(
            lambda project_data_folder_iter_: (
                Path(project_data_folder_iter_.data.details.path) ==
                Path(project_file_data.data.details.path).parent
            ),
            all_folders_list
        ))
        parent_folder_id = parent_folder_obj.id

        # If the parent folder id is not in the dictionary, add it
        if parent_folder_id not in parent_folder_dict:
            parent_folder_dict[parent_folder_id] = []

        # Add the project data to the parent folder
        parent_folder_dict[parent_folder_id].append(project_file_data)

    # Return the dictionary
    return parent_folder_dict


def handler(event, context) -> Dict[str, List[Dict[str, Union[str, List[str]]]]]:
    """
    Generate the copy objects
    :param event:
    :param context:
    :return:
    """
    # Set env vras
    set_icav2_env_vars()

    # Get inputs
    source_uri_list: List[str] = event["sourceUriList"]
    destination_uri: str = event["destinationUri"]

    # Check destination uri endswith "/"
    if not destination_uri.endswith("/"):
        raise ValueError("Destination uri must end with a '/'")

    # Coerce the source and destination uris to project data objects
    source_list: List[Dict[str, str]] = []
    recursive_copy_jobs_list: List[Dict[str, Union[str, List[str]]]] = []
    parent_destination_project_data_obj = coerce_data_id_or_uri_to_project_data_obj(
        destination_uri,
        create_data_if_not_found=True
    )

    for source_uri_iter_ in source_uri_list:
        source_project_data_obj = coerce_data_id_or_uri_to_project_data_obj(source_uri_iter_)

        # Check if the source uri is a file or a folder
        if DataType[source_project_data_obj.data.details.dataType] == DataType.FILE:
            # Easy, simple case
            source_list.append(
                {
                    "projectId": source_project_data_obj.project_id,
                    "dataId": source_project_data_obj.data.id
                }
            )
            continue

        # When source uri is a folder, it is a little more complicated
        all_source_project_data_objs = get_files_and_folders_in_project_folder_non_recursively(source_project_data_obj)
        destination_project_data_obj = create_folder_in_project(
            project_id=parent_destination_project_data_obj.project_id,
            folder_path=Path(parent_destination_project_data_obj.data.details.path) / source_project_data_obj.data.details.name,
        )
        recursive_copy_jobs_list.append(
            {
                "destinationUri": f"icav2://{destination_project_data_obj.project_id}{destination_project_data_obj.data.details.path}",
                "sourceUriList": list(map(
                    lambda project_data_iter_: f"icav2://{project_data_iter_.project_id}{project_data_iter_.data.details.path}",
                    all_source_project_data_objs
                ))
            }
        )

    return {
        "sourceDataList": source_list,
        "destinationData": {
            "projectId": parent_destination_project_data_obj.project_id,
            "dataId": parent_destination_project_data_obj.data.id
        },
        "recursiveCopyJobsUriList": recursive_copy_jobs_list
    }