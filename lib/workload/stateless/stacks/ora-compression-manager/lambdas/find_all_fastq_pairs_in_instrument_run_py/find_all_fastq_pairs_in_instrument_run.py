#!/usr/bin/env python3

"""
Find all fastq pairs in an instrument run directory

Given an icav2 or s3 uri, traverse the directory and find all fastq pairs

Returns a list of fastq pairs in the format
[
  {
    "rgid_partial": "LANE.SAMPLE_ID",
    "read1_file_uri": "",
    "read2_file_uri": ""
  }
]
"""

import typing
import boto3
from os import environ
import re
import pandas as pd

from wrapica.project_data import (
    find_project_data_bulk,
    convert_uri_to_project_data_obj,
    ProjectData, convert_project_data_obj_to_uri
)
from wrapica.enums import DataType, UriType

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient


FASTQ_REGEX_OBJ = re.compile(r"(.*?)(?:_S\d+)?(?:_L(\d{3}))?_R[12]_001.fastq.gz")


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
    environ["ICAV2_BASE_URL"] = "https://ica.illumina.com/ica/rest"
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def handler(event, context):
    """
    Handler function for the lambda
    """
    set_icav2_env_vars()

    instrument_run_folder_uri = event["instrument_run_folder_uri"]
    instrument_run_id = event["instrument_run_id"]

    # Get the project data obj
    instrument_run_folder_obj: ProjectData = convert_uri_to_project_data_obj(
        instrument_run_folder_uri
    )

    # Find all SampleSheet*.csv files in the instrument run folder
    project_data_list = find_project_data_bulk(
        project_id=instrument_run_folder_obj.project_id,
        parent_folder_id=instrument_run_folder_obj.data.id,
        data_type=DataType.FILE,
    )

    # Iterate through samplesheets
    fastq_gz_project_data_obj_list = []
    for project_data_item in project_data_list:
        if project_data_item.data.details.name.lower().endswith(".fastq.gz"):
            fastq_gz_project_data_obj_list.append(project_data_item)

    # Sort fastq list pair list
    fastq_gz_project_data_obj_list.sort(key=lambda x: x.data.details.path)

    r1_files = list(filter(
        lambda x: x.data.details.name.endswith("_R1_001.fastq.gz"),
        fastq_gz_project_data_obj_list
    ))
    r2_files = list(filter(
        lambda x: x.data.details.name.endswith("_R2_001.fastq.gz"),
        fastq_gz_project_data_obj_list
    ))

    # Check if the number of R1 and R2 files are the same
    if len(r1_files) != len(r2_files):
        raise ValueError("Number of R1 and R2 files are not the same")

    # Create the fastq pair list
    fastq_pair_list = []

    for r1_file, r2_file in zip(r1_files, r2_files):
        rgid_regex_match = FASTQ_REGEX_OBJ.fullmatch(r1_file.data.details.name)

        sample_id = rgid_regex_match.group(1)
        lane = int(rgid_regex_match.group(2))

        if sample_id == "Undetermined":
            continue

        if lane is None:
            lane = "1"

        fastq_pair_list.append({
            "rgid_partial": f"{lane}.{sample_id}",
            "read_1_file_uri": convert_project_data_obj_to_uri(r1_file),
            "read_2_file_uri": convert_project_data_obj_to_uri(r2_file)
        })

    # Assert that the all rgid_partial are unique
    assert \
        len(pd.DataFrame(fastq_pair_list)['rgid_partial'].unique().tolist()) == len(fastq_pair_list), \
        "rgid_partial are not unique"

    return fastq_pair_list


# if __name__ == "__main__":
#     # Test the handler function
#     import json
#     environ["AWS_PROFILE"] = "umccr-development"
#     environ["ICAV2_ACCESS_TOKEN_SECRET_ID"] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "instrument_run_folder_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/",
#                     "instrument_run_id": "241024_A00130_0336_BHW7MVDSXC",
#                 },
#                 None,
#             ),
#             indent=4
#         )
#     )
#
#     # [
#     #     {
#     #         "rgid_partial": "1.L2401526",
#     #         "read_1_file_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401526/L2401526_S1_L001_R1_001.fastq.gz",
#     #         "read_2_file_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401526/L2401526_S1_L001_R2_001.fastq.gz"
#     #     },
#     #     ...
#     #     {
#     #         "rgid_partial": "4.L2401553",
#     #         "read_1_file_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_4/L2401553/L2401553_S27_L004_R1_001.fastq.gz",
#     #         "read_2_file_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_4/L2401553/L2401553_S27_L004_R2_001.fastq.gz"
#     #     }
#     # ]
