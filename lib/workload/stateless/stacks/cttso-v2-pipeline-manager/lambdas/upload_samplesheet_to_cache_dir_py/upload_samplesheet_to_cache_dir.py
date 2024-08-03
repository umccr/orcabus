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
from urllib.parse import urlparse

# Samplesheet imports
from v2_samplesheet_maker.functions.v2_samplesheet_writer import v2_samplesheet_writer

# Wrapica imports
from wrapica.project_data import (
    write_icav2_file_contents,
    convert_project_data_obj_to_uri,
    get_project_data_obj_by_id
)

# V2 Imports
from cttso_v2_pipeline_manager_tools.utils.aws_ssm_helpers import set_icav2_env_vars


def handler(event, context):
    """
    Upload samplesheet csv to cache path

    Args:
        event:
        context:

    Returns:

    """

    # Check inputs are present
    cache_uri = event.get("cache_uri")
    project_id = urlparse(cache_uri).netloc
    cache_path = Path(urlparse(cache_uri).path)

    samplesheet = event.get("samplesheet")

    # Check cache path
    if not cache_uri:
        raise ValueError("cache_uri is required")
    # CHeck samplesheet dict
    if not samplesheet:
        raise ValueError("samplesheet is required")

    # Set icav2 env vars
    set_icav2_env_vars()

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
        samplesheet_file_uri = convert_project_data_obj_to_uri(
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