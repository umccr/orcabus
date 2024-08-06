#!/usr/bin/env python

"""
Given an analysis output uri,

This script will generate the expected output json for the analysis.

{
    "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240513a3fb6502/out/"
}

Yields

{
    "interop_output_dir": "",
    "multiqc_html_report": "",
    "multiqc_output_dir": "",
}

We don't use the outputs json endpoint since we cannot rely on its consistency
https://github.com/umccr-illumina/ica_v2/issues/185

Instead we just take the output uri and find the directories as expected
"""

# Standard imports
from os import environ
import typing
import boto3

# IDE imports only
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager.client import SecretsManagerClient

# ICA imports
from wrapica.enums import DataType, UriType
from wrapica.libica_models import ProjectData
from wrapica.project_data import (
    convert_icav2_uri_to_project_data_obj, convert_project_data_obj_to_uri,
    list_project_data_non_recursively
)


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
    analysis_uri = events.get("analysis_output_uri")

    # Convert analysis uri to project folder object
    analysis_project_data_obj = convert_icav2_uri_to_project_data_obj(analysis_uri)

    # Analysis list
    analysis_top_level_data_list = list_project_data_non_recursively(
        project_id=analysis_project_data_obj.project_id,
        parent_folder_id=analysis_project_data_obj.data.id,
    )

    # Get multiqc directory
    try:
        multiqc_data_obj: ProjectData = next(
            filter(
                lambda project_data_iter: (
                    project_data_iter.data.details.name == "multiqc" and
                    DataType[project_data_iter.data.details.data_type] == DataType.FOLDER
                ),
                analysis_top_level_data_list
            )
        )
    except StopIteration:
        raise ValueError(f"Multiqc directory not found in {analysis_uri}")

    # InterOp Directory
    try:
        interop_data_obj: ProjectData = next(
            filter(
                lambda project_data_iter: (
                    project_data_iter.data.details.name == "interop_summary_files" and
                    DataType[project_data_iter.data.details.data_type] == DataType.FOLDER
                ),
                analysis_top_level_data_list
            )
        )
    except StopIteration:
        raise ValueError(f"Interop directory not found in {analysis_uri}")

    # Multiqc html
    # Convert analysis uri to project folder object
    multiqc_html_data_obj: ProjectData = next(
        filter(
            lambda project_data_obj: project_data_obj.data.details.name.endswith(".html"),
            list_project_data_non_recursively(
                project_id=multiqc_data_obj.project_id,
                parent_folder_id=multiqc_data_obj.data.id,
                data_type=DataType.FILE
            )
        )
    )

    return {
        "interop_output_dir": convert_project_data_obj_to_uri(interop_data_obj, UriType.S3),
        "multiqc_html_report": convert_project_data_obj_to_uri(multiqc_html_data_obj, UriType.S3),
        "multiqc_output_dir": convert_project_data_obj_to_uri(multiqc_data_obj, UriType.S3)
    }


# if __name__ == "__main__":
#     import json
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "analysis_output_uri": "icav2://development/analysis/bclconvert-interop-qc/20240806ce5755fd/"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "interop_output_dir": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/bclconvert-interop-qc/20240806ce5755fd/interop_summary_files/",
#     #   "multiqc_html_report": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/bclconvert-interop-qc/20240806ce5755fd/multiqc/240229_A00130_0288_BH5HM2DSXC_multiqc_report.html",
#     #   "multiqc_output_dir": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/bclconvert-interop-qc/20240806ce5755fd/multiqc/"
#     # }
