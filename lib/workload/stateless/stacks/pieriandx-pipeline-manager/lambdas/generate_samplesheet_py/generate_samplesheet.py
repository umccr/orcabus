#!/usr/bin/env python3

"""
Generate a samplesheet from a cttso v2 samplesheet file

{
    "samplesheet_uri": "s3://.../Logs_Intermediates/SampleSheet_Validation/SampleSheet_Intermediate.csv"
}

Returns

{
    "samplesheet_str": ""
}

"""

# Standard imports
from typing import Dict
import logging
import boto3
from os import environ

# Custom libraries
from v2_samplesheet_maker.functions.v2_samplesheet_writer import v2_samplesheet_writer

# Local imports
from pieriandx_pipeline_tools.utils.samplesheet_helpers import read_v2_samplesheet

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

# Set loggers
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


def handler(event, context) -> Dict[str, str]:
    # Set ICAv2 env variables
    logger.info("Setting icav2 env vars from secrets manager")
    set_icav2_env_vars()

    # Get the samplesheet uri
    samplesheet_uri = event.get("samplesheet_uri", None)

    # Get the samplesheet as an icav2 projectdata object
    samplesheet_dict = read_v2_samplesheet(samplesheet_uri)

    # Convert to string (as a samplesheet)
    samplesheet_str = str(v2_samplesheet_writer(samplesheet_dict).read())

    # Replace TSO500L_Data header line
    # Sample_ID,Sample_Type,Lane,Index,Index2,I7_Index_ID,I5_Index_ID
    # With
    # Sample_ID,Sample_Type,Lane,index,index2,I7_Index_ID,I5_Index_ID
    # Without changing the Index1Cycles and Index2Cycles of the Reads section
    # Hacky and dirty workaround required because PierianDx is not able to handle Index / Index2 in uppercase
    # Assumes Index and Index2 fall within the middle of the index line
    samplesheet_str = samplesheet_str.replace(',Index', ',index')

    return {
        "samplesheet_str": samplesheet_str
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     environ['AWS_REGION'] = "ap-southeast-2"
#     environ['AWS_PROFILE'] = 'umccr-development'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "samplesheet_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
# # Yields
# # {
# #   "samplesheet_str": "[Header]\nFileFormatVersion,2\nRunName,240229_A00130_0288_BH5HM2DSXC\nInstrumentType,NovaSeq\n\n[TSO500L_Settings]\n\n\n[TSO500L_Data]\nSample_ID,index_ID,Sample_Type,index,index2,I7_Index_ID,I5_Index_ID\nL2400161,UDP0019,DNA,CCATCATTAG,AGAGGCAACC,UDP0019,UDP0019\n"
# # }

