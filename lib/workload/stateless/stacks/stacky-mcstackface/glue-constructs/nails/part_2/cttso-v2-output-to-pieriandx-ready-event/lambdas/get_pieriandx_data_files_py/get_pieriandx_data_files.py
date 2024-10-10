#!/usr/bin/env python3

"""
Given the output uri, get the data files ready to upload into the pieriandx s3 bucket

So given the output uri
's3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/'
And a sample id
'L2400161'

We would expect the following files to be returned:
{
    "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/DragenCaller/L2400161/L2400161.microsat_output.json",
    "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/Tmb/L2400161/L2400161.tmb.metrics.csv",
    "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161.cnv.vcf.gz",
    "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161.hard-filtered.vcf.gz",
    "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161_Fusions.csv",
    "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161_MetricsOutput.tsv",
    "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
}
"""

# Standard imports
from pathlib import Path
import typing
import logging
import boto3
from os import environ
from urllib.parse import urlparse, urlunparse

# Custom imports
from wrapica.project_data import convert_uri_to_project_data_obj
from wrapica.libica_exceptions import ApiException

# Typing imports
from typing import Dict
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient


# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

URL_EXTENSION_MAP = {
    "microsat_output_uri": "Logs_Intermediates/DragenCaller/{sample_id}/{sample_id}.microsat_output.json",
    "tmb_metrics_uri": "Logs_Intermediates/Tmb/{sample_id}/{sample_id}.tmb.metrics.csv",
    "cnv_vcf_uri": "Results/{sample_id}/{sample_id}.cnv.vcf.gz",
    "hard_filtered_vcf_uri": "Results/{sample_id}/{sample_id}.hard-filtered.vcf.gz",
    "fusions_uri": "Results/{sample_id}/{sample_id}_Fusions.csv",
    "metrics_output_uri": "Results/{sample_id}/{sample_id}_MetricsOutput.tsv",
    "samplesheet_uri": "Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",
}

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


def extend_url_path(base_url: str, path_ext: Path):
    """
    Given a base url, convert to a url object, extend the base url path with the path extension and return the new url
    :param base_url:
    :param path_ext:
    :return:
    """

    base_url_obj = urlparse(base_url)

    # Extend the path
    new_path = Path(base_url_obj.path).joinpath(path_ext)

    # Return the new url
    return str(urlunparse(
        (
            base_url_obj.scheme,
            base_url_obj.netloc,
            str(new_path),
            None, None, None
        )
    ))


def handler(event, context) -> Dict[str, Dict]:
    """
    Firse we need to set the icav2 env vars
    :param event:
    :param context:
    :return:
    """
    # Set ICAv2 Env Vars
    set_icav2_env_vars()

    # Get the output uri and sample id from the event dict
    output_uri = event["output_uri"]
    sample_id = event["sample_id"]

    # Get the project name and owner from the output uri

    # Camel case data_files values for the event dict
    data_files = {
        "microsatOutputUri": extend_url_path(output_uri, Path(URL_EXTENSION_MAP["microsat_output_uri"].format(sample_id=sample_id))),
        "tmbMetricsUri": extend_url_path(output_uri, Path(URL_EXTENSION_MAP["tmb_metrics_uri"].format(sample_id=sample_id))),
        "cnvVcfUri": extend_url_path(output_uri, Path(URL_EXTENSION_MAP["cnv_vcf_uri"].format(sample_id=sample_id))),
        "hardFilteredVcfUri": extend_url_path(output_uri, Path(URL_EXTENSION_MAP["hard_filtered_vcf_uri"].format(sample_id=sample_id))),
        "fusionsUri": extend_url_path(output_uri, Path(URL_EXTENSION_MAP["fusions_uri"].format(sample_id=sample_id))),
        "metricsOutputUri": extend_url_path(output_uri, Path(URL_EXTENSION_MAP["metrics_output_uri"].format(sample_id=sample_id))),
        "samplesheetUri": extend_url_path(output_uri, Path(URL_EXTENSION_MAP["samplesheet_uri"].format(sample_id=sample_id))),
    }

    # Check all data files exist
    for key, value in data_files.items():
        logger.info(f"Checking {key} exists: {value}")
        # Check the url exists
        try:
            convert_uri_to_project_data_obj(value)
        except ApiException as e:
            logger.error(f"Error checking {key} exists: {e}")
            raise e

    return {
        "data_files": data_files
    }


if __name__ == "__main__":
    import json
    from os import environ
    environ['AWS_PROFILE'] = 'umccr-development'
    environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
    environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"

    print(
        json.dumps(
            handler(
                {
                    "output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/",
                    "sample_id": "L2400160"
                },
                None
            ),
            indent=4
        )
    )

    # {
    #     "data_files": {
    #         "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/DragenCaller/L2400161/L2400161.microsat_output.json",
    #         "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/Tmb/L2400161/L2400161.tmb.metrics.csv",
    #         "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161.cnv.vcf.gz",
    #         "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161.hard-filtered.vcf.gz",
    #         "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161_Fusions.csv",
    #         "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161_MetricsOutput.tsv",
    #         "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
    #     }
    # }
