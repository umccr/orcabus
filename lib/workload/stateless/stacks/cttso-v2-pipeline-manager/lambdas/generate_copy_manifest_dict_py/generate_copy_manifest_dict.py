#!/usr/bin/env python3

"""
Given a cache path, sample id and list of fastq list rows,
generate a manifest file to copy fastq files to the cache directory

This will be launched in a downstream step

Given

{
    "cache_uri": "/path/to/cache",
    "sample_id": "sample_id",
    "fastq_list_rows": [ { "RGID": "...", "RGLB": "...", "RGSM": "sample_id", "Read1FileURI": "icav2://", "...", "Read1FileURISrc": "icav2://"} ]
    /* Except fastq list rows is b64gz encoded */
}

Return a icav2 copy files dict

{
  "dest_uri": "<cache_uri>",
  "source_uris": [
      "fastq_list_rows[0].Read1FileURI",
      "fastq_list_rows[0].Read2FileURI"
  ]
}

"""

# Standard imports
from functools import reduce
from pathlib import Path
from urllib.parse import urlparse

# Wrapica imports
from wrapica.enums import DataType
from wrapica.project_data import convert_project_id_and_data_path_to_icav2_uri


def handler(event, context):
    """

    Generate a copy manifest from fastq list rows to cache path

    Args:
        event:
        context:

    Returns:

    """

    # Get the cache path
    cache_uri = event.get("cache_uri", None)
    # Check cache path
    if cache_uri is None:
        raise ValueError("Cache uri is required")

    # Split cache uri into project id and cache path
    project_id = urlparse(cache_uri).netloc
    cache_path = Path(urlparse(cache_uri).path)

    # Get the sample id
    sample_id = event.get("sample_id", None)

    # Get fastq list rows
    fastq_list_rows = event.get("fastq_list_rows", None)

    # Check fastq list rows
    if fastq_list_rows is None:
        raise ValueError("Fastq list rows are required")

    # Generate the manifest list
    fastq_cache_path = convert_project_id_and_data_path_to_icav2_uri(
        project_id=project_id,
        data_path=Path(cache_path) / sample_id,
        data_type=DataType.FOLDER
    )

    # Filter fastq list rows by RGSM (match sample_id)
    fastq_list_rows = list(
        filter(
            lambda fastq_list_row_iter: fastq_list_row_iter.get("rgsm") == sample_id,
            fastq_list_rows
        )
    )

    # Generate source uris
    source_uris = list(
        reduce(
            # Flatten the list
            lambda row_iter_1, row_iter_2: row_iter_1 + row_iter_2,
            map(
                lambda fastq_list_row_iter: [
                    fastq_list_row_iter.get("read1FileUri"),
                    fastq_list_row_iter.get("read2FileUri")
                ],
                fastq_list_rows
            )
        )
    )

    # Return the manifest list
    return {
        "dest_uri": fastq_cache_path,
        "source_uris": source_uris
    }


# if __name__ == "__main__":
#
#     import json
#     # Test the handler
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "cache_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_cache/cttsov2/2_1_1/202405316db95e97/",
#                     "sample_id": "L2400163",
#                     "fastq_list_rows": [
#                       {
#                         "rgid": "ATGGTTGACT.AGGACAGGCC.1",
#                         "rgsm": "L2400163",
#                         "rglb": "L2400163",
#                         "lane": 1,
#                         "read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#                         "read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#                       }
#                     ]
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_cache/cttsov2/2_1_1/202405316db95e97/L2400163/",
#     #     "source_uris": [
#     #         "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#     #         "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#     #     ]
#     # }
