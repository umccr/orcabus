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
from wrapica.enums import DataType
from wrapica.libica_models import ProjectData
from wrapica.project_data import (
    convert_icav2_uri_to_project_data_obj,
    list_project_data_non_recursively, convert_project_data_obj_to_icav2_uri
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


def get_files_from_germline_directory(dragen_germline_project_data_obj: ProjectData, dragen_germline_output_prefix: str) -> Dict[str, ProjectData]:
    """
    Get the following files from the germline directory:
    dragen_germline_snv_vcf
    dragen_germline_snv_vcf_hard_filtered
    :return:
    """

    germline_files_list: typing.List[ProjectData] = list_project_data_non_recursively(
        project_id=dragen_germline_project_data_obj.project_id,
        parent_folder_id=dragen_germline_project_data_obj.data.id,
        data_type=DataType.FILE
    )

    # Collect the snv vcf
    dragen_germline_snv_vcf = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_germline_output_prefix}.vcf.gz"
            ,
            germline_files_list
        )
    )

    dragen_germline_snv_vcf_hard_filtered = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_germline_output_prefix}.hard-filtered.vcf.gz",
            germline_files_list
        )
    )

    return {
        "dragen_germline_snv_vcf": dragen_germline_snv_vcf,
        "dragen_germline_snv_vcf_hard_filtered": dragen_germline_snv_vcf_hard_filtered
    }


def get_files_from_somatic_directory(dragen_somatic_project_data_obj: ProjectData, dragen_somatic_output_prefix: str) -> Dict[str, ProjectData]:
    """
    Get the following files from the dragen somatic directory

    dragen_germline_bam
    dragen_somatic_output
    dragen_somatic_snv_vcf
    dragen_somatic_snv_vcf_hard_filtered
    dragen_somatic_sv_vcf
    dragen_somatic_bam

    :param dragen_somatic_project_data_obj:
    :param dragen_somatic_output_prefix:
    :return:
    """

    somatic_files_list: typing.List[ProjectData] = list_project_data_non_recursively(
        project_id=dragen_somatic_project_data_obj.project_id,
        parent_folder_id=dragen_somatic_project_data_obj.data.id,
        data_type=DataType.FILE
    )

    # Find the dragen germline bam as the only bam in the directory that doesn't have the somatic prefix
    # Derived instead from the germline prefix
    try:
        dragen_germline_bam = next(
            filter(
                lambda project_data_iter: project_data_iter.data.details.name.endswith("_normal.bam"),
                somatic_files_list
            )
        )
    except StopIteration:
        dragen_germline_bam = None

    # Collect the snv vcf
    dragen_somatic_snv_vcf = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_somatic_output_prefix}.vcf.gz"
            ,
            somatic_files_list
        )
    )

    dragen_somatic_snv_vcf_hard_filtered = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_somatic_output_prefix}.hard-filtered.vcf.gz",
            somatic_files_list
        )
    )

    dragen_somatic_sv_vcf = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_somatic_output_prefix}.sv.vcf.gz",
            somatic_files_list
        )
    )

    try:
        dragen_somatic_bam = next(
            filter(
                lambda project_data_iter: project_data_iter.data.details.name == f"{dragen_somatic_output_prefix}_tumor.bam",
                somatic_files_list
            )
        )
    except StopIteration:
        dragen_somatic_bam = None

    return {
        "dragen_germline_bam": dragen_germline_bam,
        "dragen_somatic_snv_vcf": dragen_somatic_snv_vcf,
        "dragen_somatic_snv_vcf_hard_filtered": dragen_somatic_snv_vcf_hard_filtered,
        "dragen_somatic_sv_vcf": dragen_somatic_sv_vcf,
        "dragen_somatic_bam": dragen_somatic_bam
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
    somatic_output_prefix = event["somatic_output_prefix"]
    germline_output_prefix = event["germline_output_prefix"]

    # Get the analysis output uri as a project data object
    analysis_output_obj = convert_icav2_uri_to_project_data_obj(analysis_output_uri)

    # FInd the dragen germline output
    top_dir_list: List[ProjectData] = list_project_data_non_recursively(
        project_id=analysis_output_obj.project_id,
        parent_folder_id=analysis_output_obj.data.id,
        data_type=DataType.FOLDER
    )

    # Get the directories
    dragen_germline_directory = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{germline_output_prefix}_dragen_germline",
            top_dir_list
        )
    )

    dragen_somatic_directory = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{somatic_output_prefix}_dragen_somatic",
            top_dir_list
        )
    )

    multiqc_directory = next(
        filter(
            lambda project_data_iter: project_data_iter.data.details.name == f"{somatic_output_prefix}__{germline_output_prefix}_dragen_somatic_and_germline_multiqc",
            top_dir_list
        )
    )

    # File outputs
    file_outputs_dict = {
        "dragen_germline_output": dragen_germline_directory,
        "dragen_somatic_output": dragen_somatic_directory,
        "multiqc_output": multiqc_directory,
    }

    # Get the files from the germline directory
    file_outputs_dict.update(get_files_from_germline_directory(dragen_germline_directory, germline_output_prefix))

    # Get the files from the somatic directory
    file_outputs_dict.update(get_files_from_somatic_directory(dragen_somatic_directory, somatic_output_prefix))

    # Get the html report from the multiqc directory
    file_outputs_dict.update(get_files_from_multiqc_directory(multiqc_directory))

    # Every value in the file outputs dict is a project data object, convert each value to a uri
    outputs_as_uri = dict(
        map(
            lambda key_val: (key_val[0], convert_project_data_obj_to_icav2_uri(key_val[1])),
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
#                     "somatic_output_prefix": "L2400195",
#                     "germline_output_prefix": "L2400191",
#                     "analysis_output_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "dragen_germline_snv_vcf": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400191_dragen_germline/L2400191.vcf.gz",
#     #     "dragen_germline_snv_vcf_hard_filtered": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400191_dragen_germline/L2400191.hard-filtered.vcf.gz",
#     #     "dragen_germline_bam": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400191_normal.bam",
#     #     "dragen_somatic_snv_vcf": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195.vcf.gz",
#     #     "dragen_somatic_snv_vcf_hard_filtered": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195.hard-filtered.vcf.gz",
#     #     "dragen_somatic_sv_vcf": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195.sv.vcf.gz",
#     #     "dragen_somatic_bam": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195_tumor.bam",
#     #     "multiqc_html_report": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195__L2400191_dragen_somatic_and_germline_multiqc/L2400195__L2400191_dragen_somatic_and_germline_multiqc.html"
#     # }


# if __name__ == "__main__":
#     from os import environ
#     import json
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "somatic_output_prefix": "CORE01050021T",
#                     "germline_output_prefix": "CORE01050021R",
#                     "analysis_output_uri": "icav2://cohort-hmf-pdac-dev/cram_test_run/out/20240729868b9d5d/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "dragen_germline_snv_vcf": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400191_dragen_germline/L2400191.vcf.gz",
#     #     "dragen_germline_snv_vcf_hard_filtered": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400191_dragen_germline/L2400191.hard-filtered.vcf.gz",
#     #     "dragen_germline_bam": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400191_normal.bam",
#     #     "dragen_somatic_snv_vcf": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195.vcf.gz",
#     #     "dragen_somatic_snv_vcf_hard_filtered": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195.hard-filtered.vcf.gz",
#     #     "dragen_somatic_sv_vcf": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195.sv.vcf.gz",
#     #     "dragen_somatic_bam": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195_dragen_somatic/L2400195_tumor.bam",
#     #     "multiqc_html_report": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/tumor_normal/202407237e0fd947/L2400195__L2400191_dragen_somatic_and_germline_multiqc/L2400195__L2400191_dragen_somatic_and_germline_multiqc.html"
#     # }
