#!/usr/bin/env python

"""
Given an analysis output uri,

This script will generate the expected output json for the analysis.

// FIXME - find an example that's in the right directory context
{
    "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/"
    "sample_id": "L2301368"
}

Yields

{
    "results_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/Results/"
    "logs_intermediates_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/Logs_Intermediates/"
    "nextflow_logs_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/TSO500_Nextflow_Logs/"
    "sample_passed": true  # Or false?
}

We don't use the outputs json endpoint since we cannot rely on its consistency
https://github.com/umccr-illumina/ica_v2/issues/185

Instead we just take the output uri (and a sample id) and find the directories as expected
"""
# Standard imports
import json
import typing
import logging
from os import environ
import boto3

# Wrapica imports
from wrapica.enums import DataType
from wrapica.libica_models import ProjectData
from wrapica.project_data import (
    convert_icav2_uri_to_project_data_obj,
    list_project_data_non_recursively, read_icav2_file_contents_to_string,
    convert_project_data_obj_to_icav2_uri
)

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


def handler(events, context):
    # Set icav2 env vars
    set_icav2_env_vars()

    # Get analysis uri
    analysis_output_uri = events.get("analysis_output_uri")

    # Get analysis uri as an object
    analysis_project_data_obj = convert_icav2_uri_to_project_data_obj(analysis_output_uri)

    # Top level list
    analysis_output_list = list_project_data_non_recursively(
        project_id=analysis_project_data_obj.project_id,
        parent_folder_id=analysis_project_data_obj.data.id,
        data_type=DataType.FOLDER
    )

    # Get sample id
    sample_id = events.get("sample_id")

    # Results Directory
    try:
        results_dir_data_obj = next(
            filter(
                lambda project_data_obj_iter: project_data_obj_iter.data.details.name == "Results",
                analysis_output_list
            )
        )
    except StopIteration:
        raise ValueError(f"Could not get results directory under {analysis_output_uri}")

    # Logs and Intermediates Directory
    try:
        logs_intermediates_dir_data_obj: ProjectData = next(
            filter(
                lambda project_data_obj_iter: project_data_obj_iter.data.details.name == "Logs_Intermediates",
                analysis_output_list
            )
        )
    except StopIteration:
        raise ValueError(f"Could not get logs intermediates directory under {analysis_output_uri}")

    # Nextflow results dir
    try:
        nextflow_logs_dir_data_obj = next(
            filter(
                lambda project_data_obj_iter: project_data_obj_iter.data.details.name == "TSO500_Nextflow_Logs",
                analysis_output_list
            )
        )
    except StopIteration:
        raise ValueError(f"Could not get nextflow logs directory under {analysis_output_uri}")

    # Check sample passed
    # Collect the `passing_sample_steps.json` file from the Logs_Intermediates directory
    # The file should contain the sample id as a key and a list of passed steps as a value
    # If the 'MetricsOutput' step is in the list of passed steps, then the sample passed
    # Otherwise, the sample failed
    try:
        passing_sample_steps_file = next(
            filter(
                lambda project_data_obj_iter: project_data_obj_iter.data.details.name == "passing_sample_steps.json",
                list_project_data_non_recursively(
                    project_id=logs_intermediates_dir_data_obj.project_id,
                    parent_folder_id=logs_intermediates_dir_data_obj.data.id,
                )
            )
        )
    except StopIteration:
        raise ValueError(f"Could not find passing sample steps file under {logs_intermediates_dir_data_obj.data.details.path}")

    # Passing sample steps dictionary
    passing_sample_steps_dict = json.loads(
        read_icav2_file_contents_to_string(
            project_id=passing_sample_steps_file.project_id,
            data_id=passing_sample_steps_file.data.id,
        )
    )
    # Check sample id is in the keys list for the passing samples steps file
    if sample_id not in passing_sample_steps_dict:
        raise ValueError(f"Sample id {sample_id} not found in passing sample steps file keys list")
    # Check the 'MetricsOutput' step is in the list of passed steps
    sample_passed = "MetricsOutput" in passing_sample_steps_dict[sample_id]

    return {
        "results_dir": convert_project_data_obj_to_icav2_uri(results_dir_data_obj),
        "logs_intermediates_dir": convert_project_data_obj_to_icav2_uri(logs_intermediates_dir_data_obj),
        "nextflow_logs_dir": convert_project_data_obj_to_icav2_uri(nextflow_logs_dir_data_obj),
        "sample_passed": sample_passed
    }


# if __name__ == "__main__":
#     import json
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-trial"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/",
#                     "sample_id": "L2301368"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "results_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/Results/",
#     #   "logs_intermediates_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/Logs_Intermediates/",
#     #   "nextflow_logs_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0028/out/TSO500_Nextflow_Logs/",
#     #   "sample_passed": true
#     # }



