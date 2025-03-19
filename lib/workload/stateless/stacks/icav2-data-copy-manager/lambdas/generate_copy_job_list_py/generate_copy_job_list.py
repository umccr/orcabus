#!/usr/bin/env python3

"""
Given a source uri and a destination uri, generate a list of copy jobs to be executed.

The source uri may be a file or a directory, the destination uri must be a directory.

Inputs are as follows:
{
    "sourceUri": "icav2://project-id/folder1/folder2/file1", OR "s3://path/to/source/folder/",
    "destinationUri": "icav2://project-id/folder1/folder2/"
}

If the source uri is a directory, we traverse the list and generate a job for every subfolder

Outputs are as follows:

[
    {
        "destinationId": "fol.123456"
        "sourceIdList": ["fil.123456", "fil.123457"]
    },
    {
    },
]


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
    find_project_data_bulk,
    ProjectData
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


def get_all_files_and_folders_in_project_folder(project_data_folder: ProjectData) -> List[ProjectData]:
    """
    Given a project data folder, return a list of all files in the folder
    """

    # Get the file list
    data_list = find_project_data_bulk(
        project_id=project_data_folder.project_id,
        parent_folder_id=project_data_folder.data.id,
    )

    # Return the list of files (and this one)
    return data_list + [project_data_folder]


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
    # Get inputs
    source_uri = event["sourceUri"]
    destination_uri = event["destinationUri"]

    # Check destination uri endswith "/"
    if not destination_uri.endswith("/"):
        raise ValueError("Destination uri must end with a '/'")

    # Coerce the source and destination uris to project data objects
    source_project_data_obj = coerce_data_id_or_uri_to_project_data_obj(source_uri)
    destination_project_data_obj = coerce_data_id_or_uri_to_project_data_obj(destination_uri, create_data_if_not_found=True)

    # Check if the source uri is a file or a folder
    if DataType[source_project_data_obj.data.details.dataType] == DataType.FILE:
        # Easy, simple case
        return {
            "copyJobList": [
                {
                    "sourceDataIdList": [source_project_data_obj.data.id],
                    "sourceProjectId": source_project_data_obj.project_id,
                    "destinationDataId": destination_project_data_obj.data.id,
                    "destinationProjectId": destination_project_data_obj.project_id
                }
            ]
        }

    # When source uri is a folder, it is a little more complicated
    all_source_project_data_objs = get_all_files_and_folders_in_project_folder(source_project_data_obj)

    # Sort the project data into parent folders
    parent_folder_dict = sort_project_data_bulk_into_parent_folders(all_source_project_data_objs)

    return {
        "copyJobList": list(map(
            lambda kv: {
                "sourceDataIdList": kv[1],  # List of source data ids
                "sourceProjectId": source_project_data_obj.project_id,
                "destinationDataId": kv[0],  # The destination folder id
                "destinationProjectId": destination_project_data_obj.project_id
            },
            parent_folder_dict
        ))
    }