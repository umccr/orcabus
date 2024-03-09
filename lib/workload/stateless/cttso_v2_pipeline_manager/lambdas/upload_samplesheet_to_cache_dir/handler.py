#!/usr/bin/env python3

"""
Upload samplesheet csv to cache path

Takes in a compressed samplesheet dict, generates the samplesheet as a CSV and then uploads it to the cache path

{
    "cache_path": "/path/to/cache",
    "project_id": "project_id",
    "samplesheet_dict_b64gz": "H4sIAAAAAAAA/8tJLS5RsjI2VrJSSU1RyC9KTS7J"
}

Returns the file id of the uploaded samplesheet

{
    "samplesheet_file_id": "fil.1234567890"
}

"""

# Standard imports
from pathlib import Path
from tempfile import NamedTemporaryFile

from wrapica.project_data import (
    write_icav2_file_contents,
    convert_project_data_obj_to_icav2_uri,
    get_project_data_obj_by_id
)

from cttso_v2_pipeline_manager_tools.utils.compression_helpers import decompress_dict
from cttso_v2_pipeline_manager_tools.utils.aws_ssm_helpers import set_icav2_env_vars

from v2_samplesheet_maker.functions.v2_samplesheet_writer import v2_samplesheet_writer


def handler(event, context):
    """
    Upload samplesheet csv to cache path

    Args:
        event:
        context:

    Returns:

    """

    # Check inputs are present
    cache_path = event.get("cache_path")
    project_id = event.get("project_id")
    samplesheet_dict_b64gz = event.get("samplesheet_dict_b64gz")

    # Check cache path
    if not cache_path:
        raise ValueError("cache_path is required")
    # Check project id
    if not project_id:
        raise ValueError("project_id is required")
    # CHeck samplesheet dict
    if not samplesheet_dict_b64gz:
        raise ValueError("samplesheet_dict_b64gz is required")

    # Set icav2 env vars
    set_icav2_env_vars()

    # Samplesheet csv str
    samplesheet_dict = decompress_dict(samplesheet_dict_b64gz)

    # Write samplesheet to file
    with NamedTemporaryFile(suffix='.csv') as samplesheet_tmp_h:
        # Write samplesheet to file
        v2_samplesheet_writer(samplesheet_dict, Path(samplesheet_tmp_h.name))

        # Generate the samplesheet as a csv
        samplesheet_file_id = write_icav2_file_contents(
            project_id=project_id,
            data_path=Path(cache_path) / "SampleSheet.csv",
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
#     samplesheet_dict_b64gz = """
# H4sIACTx5mUC/41R0WrCMBT9FcnzhCa1CttTUSgDV4bWhzFGiPZqw5pUk1Qm4r/vJtVtZXsYoZCc
# c+49veeeSQWiBEPuB2eylTXwbWOUcPwIxspGI87uBsS0mmuhAJ+ksAc9zGG9yFMWU0rj4dMcYFks
# OB3nzZHFBAukts60CrTj7rQPdciJJRzIxfdDUxs8/Y1TvjltavAIoQklVwVnv3GpS/joF0TfOOvj
# 3srZJomimltwTupd5ypKsXdgeOfu1dMiK6Z4irRIp3jw6tv2hOwfwjVU4iib1idKnJHKk0pqqVrF
# /VtB2XWrQe9chbI48RJh37mtGuP4LZyAN7gII0v4MdhqktMXOoofHmkUvhvQm7cUTqD69UysUHtc
# rCx98ZzFEY1HY3TBpfqfu9K3Nc3y1KO10HBdfojWU2mGo6cZDv6VeIik8CFgLGkW8AnvltEZrmbP
# URSxwCR/Mpe3yyfpAP0IhwIAAA==
#     """.replace("\n", "")
#
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "cache_path": "/ilmn_cttso_fastq_cache/20241231abcd1234/L12345678_run_cache",
#                     "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
#                     "samplesheet_dict_b64gz": samplesheet_dict_b64gz
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