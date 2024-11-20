#!/usr/bin/env python3

"""
Given a URI, this function returns the size of the file in bytes.
"""
import boto3
import typing
from os import environ

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

from wrapica.project_data import convert_uri_to_project_data_obj


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
    Given file_uri, convert to an icav2 projectdata object and return the size of the file in bytes.
    :param event:
    :param context:
    :return:
    """
    # Set icav2 env vars
    set_icav2_env_vars()

    # Get the file uri
    file_uri = event["file_uri"]

    # Get the file size
    return {
        "file_size": convert_uri_to_project_data_obj(file_uri).data.details.file_size_in_bytes
    }


# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "file_uri": "icav2://development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Reports/SampleSheet.csv"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "file_size": 3662
#     # }