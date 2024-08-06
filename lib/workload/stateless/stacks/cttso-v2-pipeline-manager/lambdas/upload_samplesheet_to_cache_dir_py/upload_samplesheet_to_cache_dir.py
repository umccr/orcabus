#!/usr/bin/env python3

"""
Upload samplesheet csv to cache path

Takes in a compressed samplesheet dict, generates the samplesheet as a CSV and then uploads it to the cache path

{
    "cache_uri": "icav2://project_id/path/to/cache",
    "samplesheet": "{ "header": ""... }"
}

Returns the file id of the uploaded samplesheet

{
    "samplesheet_file_id": "fil.1234567890"
}

"""

# Standard imports
from pathlib import Path
from tempfile import NamedTemporaryFile
import typing
from os import environ
import boto3

# Samplesheet imports
from v2_samplesheet_maker.functions.v2_samplesheet_writer import v2_samplesheet_writer

# Wrapica imports
from wrapica.project_data import (
    write_icav2_file_contents,
    convert_project_data_obj_to_icav2_uri,
    get_project_data_obj_by_id,
    convert_uri_to_project_data_obj
)


if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

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

def handler(event, context):
    """
    Upload samplesheet csv to cache path

    Args:
        event:
        context:

    Returns:

    """
    # Set icav2 env vars
    set_icav2_env_vars()

    # Check inputs are present
    cache_uri = event.get("cache_uri")

    # Get samplesheet json object
    samplesheet = event.get("samplesheet")

    # Convert cache uri to project data object
    cache_project_data_obj = convert_uri_to_project_data_obj(
        cache_uri,
        create_data_if_not_found=True
    )
    # Split into project id and cache path
    project_id = cache_project_data_obj.project_id
    cache_path = Path(cache_project_data_obj.data.details.path)

    # Check cache path
    if not cache_uri:
        raise ValueError("cache_uri is required")
    # CHeck samplesheet dict
    if not samplesheet:
        raise ValueError("samplesheet is required")

    # Samplesheet csv str

    # Write samplesheet to file
    with NamedTemporaryFile(suffix='.csv') as samplesheet_tmp_h:
        # Write samplesheet to file
        v2_samplesheet_writer(samplesheet, Path(samplesheet_tmp_h.name))

        # Generate the samplesheet as a csv
        samplesheet_file_id = write_icav2_file_contents(
            project_id=project_id,
            data_path=cache_path / "SampleSheet.csv",
            file_stream_or_path=Path(samplesheet_tmp_h.name)
        )

        # Get the uri for the samplesheet file
        samplesheet_file_uri = convert_project_data_obj_to_icav2_uri(
            get_project_data_obj_by_id(project_id, samplesheet_file_id)
        )

    return {
        "samplesheet_file_id": samplesheet_file_id,
        "samplesheet_file_uri": samplesheet_file_uri
    }


# if __name__ == "__main__":
#     import json
#
#     samplesheet = {
#       "header": {
#         "file_format_version": 2,
#         "run_name": "Tsqn-NebRNA231113-MLeeSTR_16Nov23",
#         "instrument_type": "NovaSeq"
#       },
#       "reads": {
#         "read_1_cycles": "151",
#         "read_2_cycles": "151",
#         "index_1_cycles": "10",
#         "index_2_cycles": "10"
#       },
#       "tso500l_settings": {
#         "adapter_read_1": "CTGTCTCTTATACACATCT",
#         "adapter_read_2": "CTGTCTCTTATACACATCT",
#         "adapter_behaviour": "trim",
#         "minimum_trimmed_read_length": 35,
#         "mask_short_reads": 35,
#         "override_cycles": "U7N1Y143;I10;I10;U7N1Y143"
#       },
#       "tso500l_data": [
#         {
#           "sample_id": "L2301346_rerun",
#           "sample_type": "DNA",
#           "lane": 2,
#           "index": "AGGTCAGATA",
#           "index2": "TATCTTGTAG",
#           "i7_index_id": "UDP0002",
#           "i5_index_id": "UDP0002"
#         }
#       ]
#     }
#
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "cache_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20241231abcd1234/L12345678_run_cache",
#                     "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
#                     "samplesheet": samplesheet
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "samplesheet_file_id": "fil.1d24b366eea949c3a86708dc3c3824cb"
#     #     "samplesheet_file_uri": "icav2://project/7595e8f2-32d3-4c76-a324-c6a85dae87b5/path/to/samplesheet.csv"
#     # }