#!/usr/bin/env python3

"""
Find all SampleSheet*.csv files in the instrument run folder

Read them in using the v2-samplesheet-parser and return the parsed data

Returns in the following format:

[
  {
    "rgid": "INDEX1.INDEX2.LANE.SAMPLE_ID.INSTRUMENT_RUN_ID",
    "rgid_partial": "LANE.SAMPLE_ID",
  }
]
"""
import typing
from io import StringIO
import boto3
from typing import List, Dict
from os import environ

from wrapica.project_data import (
    find_project_data_bulk,
    convert_uri_to_project_data_obj,
    ProjectData, read_icav2_file_contents_to_string
)
from wrapica.enums import DataType
from v2_samplesheet_maker.functions.v2_samplesheet_reader import v2_samplesheet_reader

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
    samplesheets_project_data_obj_list = []
    for project_data_item in project_data_list:
        if project_data_item.data.details.name.lower().startswith("samplesheet"):
            samplesheets_project_data_obj_list.append(project_data_item)

    # Initialise fastq list rows list
    rgids_list: List[Dict] = []

    # Read each samplesheet
    for samplesheet_project_data_obj in samplesheets_project_data_obj_list:
        # Generate a temporary file object for the samples
        samplesheet_data_dict = v2_samplesheet_reader(
            StringIO(
                read_icav2_file_contents_to_string(
                    project_id=samplesheet_project_data_obj.project_id,
                    data_id=samplesheet_project_data_obj.data.id
                )
            )
        )

        # Convert each item in the bclconvert data section to rgids
        for bclconvert_iter_ in samplesheet_data_dict["bclconvert_data"]:
            rgids_list.append(
                {
                    "rgid": f"{bclconvert_iter_['index']}.{bclconvert_iter_['index2']}.{bclconvert_iter_['lane']}.{bclconvert_iter_['sample_id']}.{instrument_run_id}",
                    "rgid_partial": f"{bclconvert_iter_['lane']}.{bclconvert_iter_['sample_id']}",
                }
            )

    return rgids_list


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
#     #         "rgid": "ACTGCTTA.AGAGGCGC.1.L2401526.241024_A00130_0336_BHW7MVDSXC",
#     #         "rgid_partial": "1.L2401526"
#     #     },
#     #     ...
#     #     {
#     #         "rgid": "TGACGAAT.GCCTACTG.4.L2401553.241024_A00130_0336_BHW7MVDSXC",
#     #         "rgid_partial": "4.L2401553"
#     #     }
#     # ]
