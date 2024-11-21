#!/usr/bin/env python3

"""
Given an output uri and a list of rgids,
Get the fastq list csv with partial rgids and read1File and read2File columns,
merge with the rgids list csv to get the full rgids and return as a json records object

[
  {
    "rgid": "...",
    "read1File": "...",
    "read2File": "..."
  }
]
"""

# Imports
import typing
from io import StringIO
import boto3
from os import environ
import re
import pandas as pd

from wrapica.project_data import (
    convert_uri_to_project_data_obj,
    ProjectData, read_icav2_file_contents, list_project_data_non_recursively
)
from wrapica.enums import DataType

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Constants
# index.index2.lane.rgsm.instrument_run_id
RGID_PARTIAL_REGEX = re.compile(r"\w+\.\w+\.(\d+.\w+).\w+")


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


def read_fastq_list_csv(project_data: ProjectData) -> pd.DataFrame:
    """
    Read the csv from the icav2
    :param project_data:
    :return:
    """
    with StringIO(read_icav2_file_contents(project_data.project_id, project_data.data.id)) as file_contents:
        return pd.read_csv(file_contents).rename(
            columns={
                "RGID": "rgid",
                "RGLB": "rglb",
                "RGSM": "rgsm",
                "Lane": "lane",
                "Read1File": "read1File",
                "Read2File": "read2File"
            }
        )


def get_icav2_file_from_folder(project_data_list: typing.List[ProjectData], file_name: str) -> ProjectData:
    """
    Get the file from the list
    :param project_data_list:
    :param file_name:
    :return:
    """
    try:
        return next(
            filter(
                lambda project_data_iter: (
                        project_data_iter.data.details.name == file_name and
                        DataType[project_data_iter.data.details.data_type] == DataType.FILE
                ),
                project_data_list
            )
        )
    except StopIteration:
        raise ValueError(f"{file_name} not found in the project data list")


def handler(event, context):
    """
    Handler function for the lambda
    """
    set_icav2_env_vars()

    instrument_run_folder_uri = event["instrument_run_folder_uri"]
    rgids_list = event["rgids_list"]

    # Get the project data obj
    instrument_run_folder_obj: ProjectData = convert_uri_to_project_data_obj(
        instrument_run_folder_uri
    )

    # Analysis list
    output_dir_project_data_list = list_project_data_non_recursively(
        project_id=instrument_run_folder_obj.project_id,
        parent_folder_id=instrument_run_folder_obj.data.id,
    )

    # Get the ora fastq list csv
    fastq_list_ora_df = read_fastq_list_csv(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_list_ora.csv")
    )

    # Get the rgids list csv
    rgids_list_df = pd.DataFrame(
        rgids_list,
        columns=["rgid_full"]
    )
    rgids_list_df["rgid_partial"] = rgids_list_df["rgid_full"].apply(
        lambda rgid_full: RGID_PARTIAL_REGEX.match(rgid_full).group(1)
    )

    # Merge the rgids list with the fastq list
    fastq_list_df = fastq_list_ora_df.merge(
        rgids_list_df,
        left_on="rgid",
        right_on="rgid_partial",
    ).drop(
        columns=[
            "rgid",
            "rgid_partial"
        ]
    ).rename(
        columns={
            "rgid_full": "rgid"
        }
    )

    # Extend read1File and read2File with the project data uri
    fastq_list_df["read_1_file_uri"] = fastq_list_df["read1File"].apply(
        lambda read1_file_iter: instrument_run_folder_uri + read1_file_iter
    )
    fastq_list_df["read_2_file_uri"] = fastq_list_df["read2File"].apply(
        lambda read1_file_iter: instrument_run_folder_uri + read1_file_iter
    )
    fastq_list_df.drop(
        columns=[
            "read1File",
            "read2File"
        ],
        inplace=True
    )

    return fastq_list_df.to_dict(orient="records")


# if __name__ == "__main__":
#     # Test the handler function
#     import json
#     environ["AWS_PROFILE"] = "umccr-development"
#     environ["ICAV2_ACCESS_TOKEN_SECRET_ID"] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "instrument_run_folder_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411186290aa4m/",
#                     "rgids_list": [
#                         "ACTGCTTA.AGAGGCGC.1.L2401526.241024_A00130_0336_BHW7MVDSXC",
#                         "TGACGAAT.GCCTACTG.4.L2401553.241024_A00130_0336_BHW7MVDSXC"
#                     ]
#                 },
#                 None,
#             ),
#             indent=4
#         )
#     )
#
#     # [
#     #     {
#     #         "rglb": "UnknownLibrary",
#     #         "rgsm": "L2401526",
#     #         "lane": 1,
#     #         "read_1_file_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411186290aa4m/Samples/Lane_1/L2401526/L2401526_S1_L001_R1_001.fastq.ora",
#     #         "read_2_file_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411186290aa4m/Samples/Lane_1/L2401526/L2401526_S1_L001_R2_001.fastq.ora",
#     #         "rgid": "ACTGCTTA.AGAGGCGC.1.L2401526.241024_A00130_0336_BHW7MVDSXC"
#     #     },
#     #     {
#     #         "rglb": "UnknownLibrary",
#     #         "rgsm": "L2401553",
#     #         "lane": 4,
#     #         "read_1_file_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411186290aa4m/Samples/Lane_4/L2401553/L2401553_S27_L004_R1_001.fastq.ora",
#     #         "read_2_file_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411186290aa4m/Samples/Lane_4/L2401553/L2401553_S27_L004_R2_001.fastq.ora",
#     #         "rgid": "TGACGAAT.GCCTACTG.4.L2401553.241024_A00130_0336_BHW7MVDSXC"
#     #     }
#     # ]



