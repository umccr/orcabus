#!/usr/bin/env python3

"""
Get cache and output paths for cttsov2 workflow

Given inputs
{
    "project_id": "project_id",  # Required - the project id
    "portal_run_id": "20241231abcd1234",  # Optional - generated if not provided
    "sample_id": "L12345678",  # Required - the library id
}

Returns outputs
{
    "cache_path": "//cache/20241231abcd1234/L12345678_run_cache/,
    "output_path": "/mnt/scratch/output/20241231abcd1234",
    "cache_uri": "icav2://path/to/cache/20241231abcd1234/L12345678_run_cache/"
    "output_uri": "icav2://path/to/output/20241231abcd1234/"
}

"""
from pathlib import Path

from wrapica.enums import DataType
from wrapica.project_data import convert_project_id_and_data_path_to_icav2_uri

# Local imports
from cttso_v2_pipeline_manager_tools import generate_portal_run_id
from cttso_v2_pipeline_manager_tools.utils.path_helpers import (
    generate_sample_cache_path, generate_output_path
)


def handler(event, context):
    """
    Given an event dict with portal_run_id and sample_id, return the cache and output paths for the cttsov2 workflow
    Args:
        event:
        context:

    Returns:

    """

    # Get the project id
    project_id = event.get("project_id", None)

    # Get the portal_run_id and sample_id from the event
    if event.get("portal_run_id", None) is not None:
        portal_run_id = event.get("portal_run_id")
    else:
        portal_run_id = generate_portal_run_id()

    # Get the sample id
    if event.get("sample_id", None) is not None:
        sample_id = event.get("sample_id")
    else:
        raise ValueError("sample_id is required")

    # Generate the cache path for this sample
    cache_path = generate_sample_cache_path(portal_run_id, sample_id)

    # Generate the output path for this sample
    output_path = generate_output_path(portal_run_id)

    # Return cache and output paths
    return {
        "cache_path": str(cache_path),
        "output_path": str(output_path),
        "cache_uri": convert_project_id_and_data_path_to_icav2_uri(
            project_id,
            Path(cache_path),
            data_type=DataType.FOLDER
        ),
        "output_uri": convert_project_id_and_data_path_to_icav2_uri(
            project_id,
            Path(output_path),
            data_type=DataType.FOLDER
        )
    }


# if __name__ == "__main__":
#     import json
#
#     # Test the handler with portal_run_id
#     event = {
#         "project_id": "project_id",
#         "portal_run_id": "20241231abcd1234",
#         "sample_id": "L12345678"
#     }
#     print(json.dumps(handler(event, None), indent=4))
#
#     # Test the handler without portal_run_id
#     event = {
#         "project_id": "project_id",
#         "sample_id": "L12345678"
#     }
#     print(json.dumps(handler(event, None), indent=4))
#
#     """
#     {
#         "cache_path": "/ilmn_cttso_fastq_cache/20241231abcd1234/L12345678_run_cache",  /* pragma: allowlist secret */
#         "output_path": "/ilmn_cttso_fastq_cache/20241231abcd1234",
#         "cache_uri": "icav2://project_id/ilmn_cttso_fastq_cache/20241231abcd1234/L12345678_run_cache/",
#         "output_uri": "icav2://project_id/ilmn_cttso_fastq_cache/20241231abcd1234/"
#     }
#     {
#         "cache_path": "/ilmn_cttso_fastq_cache/2024030527c5a3d4/L12345678_run_cache",  /* pragma: allowlist secret */
#         "output_path": "/ilmn_cttso_fastq_cache/2024030527c5a3d4",
#         "cache_uri": "icav2://project_id/ilmn_cttso_fastq_cache/2024030527c5a3d4/L12345678_run_cache/",
#         "output_uri": "icav2://project_id/ilmn_cttso_fastq_cache/2024030527c5a3d4/"
#     }
#     """
