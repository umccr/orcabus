#!/usr/bin/env python3

"""
Set the output json

Given the following inputs, return the following outputs:
analysis_output_uri: "icav2://path/to/data"

Outputs:
dragen_germline_output
dragen_germline_snv_vcf
dragen_germline_snv_vcf_hard_filtered
dragen_germline_bam
dragen_somatic_output
dragen_somatic_snv_vcf
dragen_somatic_snv_vcf_hard_filtered
dragen_somatic_sv_vcf
dragen_somatic_bam
multiqc_output
multiqc_html_report
"""

# Standard imports
from os import environ
import typing
import boto3
import logging

from typing import Dict, List

# ICA imports
from wrapica.enums import DataType, UriType
from wrapica.libica_models import ProjectData
from wrapica.project_data import (
    convert_uri_to_project_data_obj,
    list_project_data_non_recursively, convert_project_data_obj_to_uri
)

# IDE imports only
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager.client import SecretsManagerClient

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

# Set logger
logging.basicConfig(
    level=logging.INFO,
    force=True,
    format='%(asctime)s %(message)s'
)
logger = logging.getLogger()


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


def get_files_from_transcriptome_directory(dragen_transcriptome_project_data_obj: ProjectData, dragen_output_prefix: str) -> Dict[str, ProjectData]:
    """
    Get the following files from the germline directory:
    dragen_germline_snv_vcf
    dragen_germline_snv_vcf_hard_filtered
    :return:
    """

    transcriptome_files_list: typing.List[ProjectData] = list_project_data_non_recursively(
        project_id=dragen_transcriptome_project_data_obj.project_id,
        parent_folder_id=dragen_transcriptome_project_data_obj.data.id,
        data_type=DataType.FILE
    )

    # Collect the snv vcf
    dragen_transcriptome_fusion_candidates_vcf = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_output_prefix}.fusion_candidates.vcf.gz"
            ,
            transcriptome_files_list
        )
    )

    dragen_transcriptome_bam = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_output_prefix}.bam",
            transcriptome_files_list
        )
    )

    return {
        "dragen_transcriptome_bam": dragen_transcriptome_bam,
        "dragen_transcriptome_fusion_candidates_vcf": dragen_transcriptome_fusion_candidates_vcf
    }


def get_files_from_arriba_directory(arriba_project_data_obj: ProjectData) -> Dict[str, ProjectData]:
    """
    Get the following files from the germline directory:
    arriba_html_report
    :return:
    """

    arriba_files_list: typing.List[ProjectData] = list_project_data_non_recursively(
        project_id=arriba_project_data_obj.project_id,
        parent_folder_id=arriba_project_data_obj.data.id,
        data_type=DataType.FILE
    )

    # Find the dragen germline bam as the only bam in the directory that doesn't have the somatic prefix
    # Derived instead from the germline prefix
    arriba_fusions_tsv = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == "fusions.tsv",
            arriba_files_list
        )
    )

    return {
        "arriba_fusions_tsv": arriba_fusions_tsv
    }


def get_files_from_qualimap_directory(qualimap_project_data_obj: ProjectData) -> Dict[str, ProjectData]:
    """
    Get the following files from the germline directory:
    qualimap_html_report
    :return:
    """

    qualimap_files_list: typing.List[ProjectData] = list_project_data_non_recursively(
        project_id=qualimap_project_data_obj.project_id,
        parent_folder_id=qualimap_project_data_obj.data.id,
        data_type=DataType.FILE
    )

    # Find the dragen germline bam as the only bam in the directory that doesn't have the somatic prefix
    # Derived instead from the germline prefix
    qualimap_html_report = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name.endswith(".html"),
            qualimap_files_list
        )
    )

    return {
        "qualimap_html_report": qualimap_html_report
    }


def get_files_from_multiqc_directory(multiqc_project_data_obj: ProjectData) -> Dict[str, ProjectData]:
    """
    Get the following files from the multiqc directory

    multiqc_html_report

    :param multiqc_project_data_obj:
    :return:
    """

    multiqc_files_list: typing.List[ProjectData] = list_project_data_non_recursively(
        project_id=multiqc_project_data_obj.project_id,
        parent_folder_id=multiqc_project_data_obj.data.id,
        data_type=DataType.FILE
    )

    # Find the dragen germline bam as the only bam in the directory that doesn't have the somatic prefix
    # Derived instead from the germline prefix
    multiqc_html_report = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name.endswith(".html"),
            multiqc_files_list
        )
    )

    return {
        "multiqc_html_report": multiqc_html_report
    }


def handler(event, context):
    """
    Generate a payload for the complete event to be relayed by the workflow manager
    :param event:
    :param context:
    :return:
    """
    # Set the icav2 env vars
    set_icav2_env_vars()

    # Get the analysis output uri attribute from the event
    analysis_output_uri = event["analysis_output_uri"]
    output_prefix = event["output_prefix"]

    # Get the analysis output uri as a project data object
    analysis_output_obj = convert_uri_to_project_data_obj(analysis_output_uri)

    # FInd the dragen germline output
    top_dir_list: List[ProjectData] = list_project_data_non_recursively(
        project_id=analysis_output_obj.project_id,
        parent_folder_id=analysis_output_obj.data.id,
        data_type=DataType.FOLDER
    )

    # Get the directories
    arriba_directory = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{output_prefix}_arriba",
            top_dir_list
        )
    )

    dragen_transcriptome_directory = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{output_prefix}_dragen_transcriptome",
            top_dir_list
        )
    )

    qualimap_directory = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{output_prefix}_qualimap",
            top_dir_list
        )
    )

    multiqc_directory = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{output_prefix}_dragen_transcriptome_multiqc",
            top_dir_list
        )
    )

    # File outputs
    file_outputs_dict = {
        "arriba_output": arriba_directory,
        "dragen_transcriptome_output": dragen_transcriptome_directory,
        "qualimap_output": qualimap_directory,
        "multiqc_output": multiqc_directory,
    }

    # Get the files from the transcriptome directory
    file_outputs_dict.update(get_files_from_transcriptome_directory(dragen_transcriptome_directory, output_prefix))

    # Get the files from the qualimap directory
    file_outputs_dict.update(get_files_from_qualimap_directory(qualimap_directory))

    # Get the files from the arriba directory
    file_outputs_dict.update(get_files_from_arriba_directory(arriba_directory))

    # Get the html report from the multiqc directory
    file_outputs_dict.update(get_files_from_multiqc_directory(multiqc_directory))

    # Every value in the file outputs dict is a project data object, convert each value to a uri
    outputs_as_uri = dict(
        map(
            lambda key_val: (key_val[0], convert_project_data_obj_to_uri(key_val[1], uri_type=UriType.S3)),
            file_outputs_dict.items()
        )
    )

    return outputs_as_uri


# if __name__ == "__main__":
#     from os import environ
#     import json
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "output_prefix": "L2400255",
#                     "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "arriba_output": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_arriba/",
#     #     "dragen_transcriptome_output": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_dragen_transcriptome/",
#     #     "qualimap_output": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_qualimap/",
#     #     "multiqc_output": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_dragen_transcriptome_multiqc/",
#     #     "dragen_transcriptome_bam": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_dragen_transcriptome/L2400255.bam",
#     #     "dragen_transcriptome_fusion_candidates_vcf": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_dragen_transcriptome/L2400255.fusion_candidates.vcf.gz",
#     #     "qualimap_html_report": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_qualimap/qualimapReport.html",
#     #     "arriba_fusions_tsv": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_arriba/fusions.tsv",
#     #     "multiqc_html_report": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wts/2024083105106d48/L2400255_dragen_transcriptome_multiqc/L2400255_dragen_transcriptome_multiqc.html"
#     # }
