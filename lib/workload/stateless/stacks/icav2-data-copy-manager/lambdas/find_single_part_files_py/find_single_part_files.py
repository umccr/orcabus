#!/usr/bin/env python3

"""
Given a list of icav2 project data objects (project id / data id),
find those that are uploaded as a single-part file (eTag does not contain a dash).
"""

# Standard imports
from typing import List, Dict, Union
import typing
import re
import logging
import boto3
from os import environ

# Wrapica imports
from wrapica.project_data import (
    get_project_data_obj_by_id
)

# Set logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"
MULTI_PART_ETAG_REGEX = re.compile(r"\w+-\d+")


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


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate the copy objects
    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    # Get inputs
    data_list: List[Dict[str, str]] = event["dataList"]

    single_part_files_list = []
    multi_part_files_list = []

    for source_data_dict in data_list:
        project_data_obj = get_project_data_obj_by_id(
            project_id=source_data_dict.get("projectId"),
            data_id=source_data_dict.get("dataId"),
        )

        if MULTI_PART_ETAG_REGEX.fullmatch(project_data_obj.data.details.object_e_tag) is not None:
            multi_part_files_list.append(source_data_dict)
        else:
            single_part_files_list.append(source_data_dict)


    return {
        "multiPartDataList": multi_part_files_list,
        "singlePartDataList": single_part_files_list,
    }


# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ["ICAV2_ACCESS_TOKEN_SECRET_ID"] = "ICAv2JWTKey-umccr-prod-service-production"
#
#     print(json.dumps(
#         handler(
#             {
#                 "dataList": [
#                     {
#                         "projectId": "eba5c946-1677-441d-bbce-6a11baadecbb",
#                         "dataId": "fil.be1b0cc74abe44c919a008dd6f300f84"
#                     },
#                     {
#                         "projectId": "eba5c946-1677-441d-bbce-6a11baadecbb",
#                         "dataId": "fil.d6a98abe0fed4185608d08dd6cb7632e"
#                     }
#                 ]
#             },
#             None)
#         , indent=4
#     ))
#
#     # {
#     #     "multiPartDataList": [],
#     #     "singlePartDataList": [
#     #         {
#     #             "projectId": "eba5c946-1677-441d-bbce-6a11baadecbb",
#     #             "dataId": "fil.be1b0cc74abe44c919a008dd6f300f84"
#     #         },
#     #         {
#     #             "projectId": "eba5c946-1677-441d-bbce-6a11baadecbb",
#     #             "dataId": "fil.d6a98abe0fed4185608d08dd6cb7632e"
#     #         }
#     #     ]
#     # }