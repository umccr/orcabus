#!/usr/bin/env python3

"""
Given an icav2 uri, find all the vcf files in the directory and return a list of the files.
"""

# Standard imports
import typing
from os import environ

import boto3
from typing import List

# Wrapica imports
from wrapica.enums import DataType
from wrapica.libica_models import ProjectData

from wrapica.project_data import (
    find_project_data_bulk,
    convert_uri_to_project_data_obj,
    convert_project_data_obj_to_uri
)

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


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


def handler(event, context):
    """
    Use the project data bulk command to find all vcf files in the directory and zip them all up
    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    icav2_uri = event.get("icav2_uri")

    data_obj: ProjectData = convert_uri_to_project_data_obj(icav2_uri)

    all_project_data: List[ProjectData] = find_project_data_bulk(
        project_id=data_obj.project_id,
        parent_folder_id=data_obj.data.id,
        data_type=DataType.FILE
    )

    return {
        "vcf_icav2_uri_list": list(
            map(
                lambda project_data_iter: convert_project_data_obj_to_uri(project_data_iter),
                filter(
                    lambda project_data_iter: (
                        # Is a vcf file
                        (
                            (
                                project_data_iter.data.details.path.endswith(".vcf") or
                                project_data_iter.data.details.path.endswith(".gvcf")
                            ) and
                            DataType[project_data_iter.data.details.data_type] == DataType.FILE
                        )
                        and not  # .vcf.gz does not exist
                        any(
                            map(
                                lambda project_data_gzip_iter: (
                                    project_data_gzip_iter.data.details.path == (project_data_iter.data.details.path + ".gz")
                                ),
                                all_project_data
                            )
                        )
                    ),
                    all_project_data
                )
            )
        )
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "icav2_uri": "icav2://development/analysis/cttsov2/20240714fbf1848e/"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # {
#     #   "vcf_icav2_uri_list": [
#     #     "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240621ee2db947/Logs_Intermediates/DragenCaller/L2400159/L2400159.cnv.vcf",
#     #     "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240621ee2db947/Logs_Intermediates/DragenCaller/L2400159/L2400159.hard-filtered.vcf",
#     #     "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240621ee2db947/Logs_Intermediates/DragenCaller/L2400159/L2400159.raw.hard-filtered.vcf",
#     #     "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240621ee2db947/Logs_Intermediates/DragenCaller/L2400159/L2400159.sv.vcf",
#     #     "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240621ee2db947/Logs_Intermediates/Tmb/L2400159/L2400159.hard-filtered.vcf",
#     #     "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240621ee2db947/Results/L2400159/L2400159.cnv.vcf"
#     #   ]
#     # }
