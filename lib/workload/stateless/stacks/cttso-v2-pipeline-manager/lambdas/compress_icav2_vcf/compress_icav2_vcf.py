#!/usr/bin/env python


"""
Given an icav2 uri, convert from vcf to compressed vcf

Then generate an index file for the compressed vcf

Rather than download + upload, we can stream a vcf through bzip2
"""
from pathlib import Path
import boto3
import subprocess
from tempfile import TemporaryDirectory
import logging
import typing
from os import environ

from wrapica.project_data import (
    write_icav2_file_contents, read_icav2_file_contents,
    convert_uri_to_project_data_obj, delete_project_data
)

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

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


def write_icav2_vcf_file_to_compressed_output(icav2_uri: str, output_path: Path):
    """
    ICAv2 VCF File
    :param icav2_uri:
    :param output_path:
    :return:
    """
    # Download decompressed file
    project_data_obj = convert_uri_to_project_data_obj(icav2_uri)

    # Write to output file
    read_icav2_file_contents(project_data_obj.project_id, project_data_obj.data.id, output_path.with_suffix(''))

    # Bgzip the file
    bgzip_proc = subprocess.run(
        [
            "bgzip", output_path.with_suffix('')
        ],
        capture_output=True
    )

    if bgzip_proc.returncode != 0:
        logger.error(f"Error bgzipping file: {bgzip_proc.stderr.decode()}")
        raise ChildProcessError

    # Check the output path is a file
    if not output_path.is_file():
        raise FileNotFoundError(f"File not found: {output_path}")


def generate_index_file_for_compressed_vcf(output_path: Path):
    tabix_proc = subprocess.run(
        [
            "tabix",
            "-p", "vcf",
            output_path
        ],
        capture_output=True
    )

    if tabix_proc.returncode != 0:
        logger.error(f"Error generating tabix index: {tabix_proc.stderr.decode()}")
        raise ChildProcessError


def compress_icav2_vcf_and_upload(icav2_uri):
    """
    Compress ICAv2 VCF File and index

    Delete the original decompressed vcf file.
    :param icav2_uri:
    :return:
    """
    project_data_obj = convert_uri_to_project_data_obj(icav2_uri)

    with TemporaryDirectory() as temp_dir:
        # Initialise parameters
        vcf_icav2_file_path = Path(project_data_obj.data.details.path)
        temp_vcf_output_path = Path(temp_dir) / vcf_icav2_file_path.name
        temp_vcf_compressed_output_path = temp_vcf_output_path.with_suffix(".gz").with_stem(temp_vcf_output_path.name)
        temp_vcf_compressed_output_index_path = temp_vcf_output_path.with_suffix(".tbi").with_stem(temp_vcf_compressed_output_path.name)

        # Download index and tabix
        write_icav2_vcf_file_to_compressed_output(icav2_uri, temp_vcf_compressed_output_path)
        generate_index_file_for_compressed_vcf(temp_vcf_compressed_output_path)

        # Upload compressed and index file
        write_icav2_file_contents(
            project_id=project_data_obj.project_id,
            data_path=vcf_icav2_file_path.parent / temp_vcf_compressed_output_path.name,
            file_stream_or_path=temp_vcf_compressed_output_path
        )

        # Upload index
        write_icav2_file_contents(
            project_id=project_data_obj.project_id,
            data_path=vcf_icav2_file_path.parent / temp_vcf_compressed_output_index_path.name,
            file_stream_or_path=temp_vcf_compressed_output_index_path
        )

        # Delete uncompressed vcf from icav2
        delete_project_data(
            project_id=project_data_obj.project_id,
            data_id=project_data_obj.data.id
        )


def handler(event, context):
    """
    Given a vcf uri, download, compress and re-upload to icav2
    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    # Get the vcf uri
    vcf_icav2_uri = event.get("vcf_icav2_uri")

    # Compress icav2 vcf then upload compressed back to icav2
    compress_icav2_vcf_and_upload(vcf_icav2_uri)


# if __name__ == "__main__":
#     import json
#     from os import environ
#     from datetime import datetime
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print("Starting at %s" % datetime.now().isoformat())
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "vcf_icav2_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240718ff7a0cbc/Results/L2400161/L2400161.hard-filtered.gvcf"
#                 },
#                 None
#             )
#         )
#     )
#     print("Ended at %s" % datetime.now().isoformat())
