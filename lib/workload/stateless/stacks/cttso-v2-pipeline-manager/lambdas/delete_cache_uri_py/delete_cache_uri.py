#!/usr/bin/env python3

"""
Given a sample id and a cache uri

{
    "sample_id": "L2301368",
    "cache_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20240510abcd0026/L2301368_run_cache/"
}

Checks that the cache_uri is a valid directory and contains the directory:
cache_uri / sample_id
and the file
cache_uri / SampleSheet.csv

"""
from wrapica.enums import DataType
from wrapica.project_data import (
    convert_icav2_uri_to_data_obj, list_project_data_non_recursively, delete_project_data
)
from cttso_v2_pipeline_manager_tools.utils.aws_ssm_helpers import set_icav2_env_vars


def handler(event, context):
    """
    Import
    Args:
        event:
        context:

    Returns:

    """
    set_icav2_env_vars()

    # Part 0 - get inputs
    sample_id = event.get("sample_id", None)
    cache_uri = event.get("cache_uri", None)

    # Check sample id
    if sample_id is None:
        raise ValueError("No sample_id provided")

    # Check cache uri
    if cache_uri is None:
        raise ValueError("No cache_uri provided")

    # Part 1 - check that in the cache uri, only the sample_id directory exists along with the file SampleSheet.csv
    cache_obj = convert_icav2_uri_to_data_obj(cache_uri)

    cache_folder_list = list_project_data_non_recursively(
        project_id=cache_obj.project_id,
        parent_folder_id=cache_obj.data.id,
    )

    # Check that the sample_id directory exists
    try:
        sample_folder_obj = next(
            filter(
                lambda project_data_obj_iter: project_data_obj_iter.data.details.name == sample_id,
                cache_folder_list
            )
        )
    except StopIteration:
        raise ValueError(f"Sample folder {sample_id} does not exist in cache uri {cache_uri}")

    # Confirm that only fastq files exist inside the sample folder obj
    sample_folder_list = list_project_data_non_recursively(
        project_id=cache_obj.project_id,
        parent_folder_id=sample_folder_obj.data.id,
    )

    try:
        not_fastq_file_obj = next(
            filter(
                lambda project_data_obj_iter: (
                        (not project_data_obj_iter.data.details.name.endswith(".fastq.gz")) or
                        (not DataType[project_data_obj_iter.data.details.data_type] == DataType.FILE)
                ),
                sample_folder_list
            )
        )
    except StopIteration:
        # We expect to get here, we do not expect any non-fastq files in the sample folder
        pass
    else:
        raise ValueError(
            f"Non-fastq file {not_fastq_file_obj.data.details.name} exists in the "
            f"sample folder {sample_id} in cache uri {cache_uri}"
        )

    # Check that the SampleSheet.csv file exists
    try:
        sample_sheet_csv_obj = next(
            filter(
                lambda project_data_obj_iter: project_data_obj_iter.data.details.name == "SampleSheet.csv",
                cache_folder_list
            )
        )
    except StopIteration:
        raise ValueError(f"SampleSheet.csv does not exist in the cache uri {cache_uri}")

    # Check that the directory has two entries overall
    if not len(cache_folder_list) == 2:
        raise ValueError(
            f"Expected two entries in the cache folder list, SampleSheet.csv and the sample_id directory "
            f"but got {len(cache_folder_list)}: "
            f"{', '.join([project_data_obj.data.details.name for project_data_obj in cache_folder_list])}"
        )

    # Delete the cache directory
    delete_project_data(
        project_id=cache_obj.project_id,
        data_id=cache_obj.data.id,
    )


# if __name__ == "__main__":
#     import json
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-trial"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "sample_id": "L2301368",
#                     "cache_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20240510abcd0026/L2301368_run_cache/"
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#     # null
