#!/usr/bin/env python

"""
Given an analysis output uri,

This script will generate the expected output json for the analysis.

{
    "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240513a3fb6502/out/"
}

Yields

{
    "dragen_alignment_output_directory": "",
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
import logging

# ICA imports
from wrapica.enums import DataType, UriType
from wrapica.libica_models import ProjectData
from wrapica.project_data import (
    convert_uri_to_project_data_obj, convert_project_data_obj_to_uri,
    list_project_data_non_recursively
)


# IDE imports only
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager.client import SecretsManagerClient


# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


# Set logger
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
    analysis_project_data_obj = convert_uri_to_project_data_obj(analysis_uri)

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
                    project_data_iter.data.details.name.endswith("_multiqc") and
                    DataType(project_data_iter.data.details.data_type) == DataType.FOLDER
                ),
                analysis_top_level_data_list
            )
        )
    except StopIteration:
        raise ValueError(f"Multiqc directory not found in {analysis_uri}")

    # Alignment Output Directory
    try:
        alignment_data_obj: ProjectData = next(
            filter(
                lambda project_data_iter: (
                    project_data_iter.data.details.name.endswith("_dragen_alignment") and
                    DataType(project_data_iter.data.details.data_type) == DataType.FOLDER
                ),
                analysis_top_level_data_list
            )
        )
    except StopIteration:
        raise ValueError(f"Alignment output directory not found in {analysis_uri}")

    # Get the bam file from the alignment output directory
    try:
        bam_file_obj: ProjectData = next(
            filter(
                lambda project_data_obj_iter: project_data_obj_iter.data.details.name.endswith(".bam"),
                list_project_data_non_recursively(
                    project_id=alignment_data_obj.project_id,
                    parent_folder_id=alignment_data_obj.data.id,
                    data_type=DataType.FILE
                )
            )
        )
    except StopIteration:
        bam_file_obj: None = None
        logging.warning("No bam file found")

    # Multiqc html
    # Convert analysis uri to project folder object
    multiqc_html_data_obj: ProjectData = next(
        filter(
            lambda project_data_obj_iter: project_data_obj_iter.data.details.name.endswith(".html"),
            list_project_data_non_recursively(
                project_id=multiqc_data_obj.project_id,
                parent_folder_id=multiqc_data_obj.data.id,
                data_type=DataType.FILE
            )
        )
    )

    return {
        "alignment_output_uri": convert_project_data_obj_to_uri(alignment_data_obj, UriType.S3),
        "bam_file_uri": convert_project_data_obj_to_uri(bam_file_obj, UriType.S3) if bam_file_obj else None,
        "multiqc_html_report": convert_project_data_obj_to_uri(multiqc_html_data_obj, UriType.S3),
        "multiqc_output_uri": convert_project_data_obj_to_uri(multiqc_data_obj, UriType.S3)
    }

# if __name__ == "__main__":
#     import json
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-trial"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240513a3fb6502/out/"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "interop_output_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240513a3fb6502/out/interop_summary_files/",
#     #   "multiqc_html_report": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240513a3fb6502/out/multiqc/231116_A01052_0172_BHVLM5DSX7_multiqc_report.html",
#     #   "multiqc_output_dir": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240513a3fb6502/out/multiqc/"
#     # }


# S3 Test
# if __name__ == "__main__":
#     import json
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgtsQc/20240806541adbcb/"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # {
#     #   "alignment_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgtsQc/20240806541adbcb/L2400254_dragen_alignment/",
#     #   "bam_file_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgtsQc/20240806541adbcb/L2400254_dragen_alignment/L2400254.bam",
#     #   "multiqc_html_report": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgtsQc/20240806541adbcb/L2400254_dragen_alignment_multiqc/L2400254_dragen_alignment_multiqc.html",
#     #   "multiqc_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgtsQc/20240806541adbcb/L2400254_dragen_alignment_multiqc/"
#     # }
