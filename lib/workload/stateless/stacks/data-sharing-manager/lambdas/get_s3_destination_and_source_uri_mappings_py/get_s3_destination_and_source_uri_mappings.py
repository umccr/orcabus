#!/usr/bin/env python3


# Imports
from pathlib import Path
from urllib.parse import urlunparse, urlparse

import pandas as pd
from typing import List, Dict

from data_sharing_tools.utils.dynamodb_helpers import query_dynamodb_table


def get_data_from_dynamodb(job_id: str, context: str) -> pd.DataFrame:
    """
    Given a job id, query the dynamodb table to get all data that belongs to that job id for that given data type,
    where data type is one of:
     * library
     * fastq
     * workflow
     * files
    :param job_id:
    :param context:
    :return:
    """

    # If not library, we grab the metadata anyway since we merge it on the other data types.
    return pd.DataFrame(
        query_dynamodb_table(
            job_id,
            context
        )
    )


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Given the following inputs:
      * jobId
      * pushLocation

    Generate the following outputs:
      * destinationAndSourceUriMappingsList

    This performs the following:
    * Queries the files in the dynamodb database for this packaging job id
    * For each subfolder, it generates a destination and source uri mapping based on a common parent location
    * Returns the destination and source uri mappings list for each folder
    :param event:
    :param context:
    :return:
    """

    # Extract the jobId and pushLocation from the event
    job_id = event.get("packagingJobId")
    push_location = event.get("pushLocation")

    # Check if the jobId and pushLocation are provided
    if not job_id or not push_location:
        raise ValueError("jobId and pushLocation are required")

    # Get the push location as a url object
    push_location_url_obj = urlparse(push_location)

    # Confirm the push location is a valid s3 url
    if push_location_url_obj.scheme != "s3":
        raise ValueError(f"Error: pushLocation must be a valid s3 url, {push_location} does not start with s3://")
    if not push_location_url_obj.netloc:
        raise ValueError(f"Error: pushLocation must be a valid s3 url, {push_location} does not have a bucket name")
    if not push_location_url_obj.path:
        raise ValueError(f"Error: pushLocation must be a valid s3 url, {push_location} does not have a path")

    # Initialize the destination and source uri mappings list
    destination_and_source_uri_mappings_list: List[Dict[str, str]] = []

    # Get the data from DynamoDB
    data_df = get_data_from_dynamodb(
        job_id=job_id,
        context="file"
    )

    # Calculate the relative parent path for all source files
    data_df["relativePathParent"] = data_df.apply(
        lambda row_iter_: str(Path(row_iter_['relativePath']).parent),
        axis='columns'
    )

    # Group by parent path and collect the relative paths
    for relative_path_parent, relative_path_parent_df in data_df.groupby("relativePathParent"):
        # Generate the destination and source uri mappings
        destination_and_source_uri_mappings_list.append(
            {
                "destinationUri": str(urlunparse((
                    push_location_url_obj.scheme,
                    push_location_url_obj.netloc,
                    str(Path(push_location_url_obj.path) / relative_path_parent).lstrip("/"),
                    None, None, None
                ))),
                "sourceUrisList": list(relative_path_parent_df.apply(
                    lambda row_iter_: str(urlunparse((
                        "s3",
                        row_iter_['bucket'],
                        row_iter_['key'],
                        None, None, None
                    ))),
                    axis='columns'
                ))
            }
        )

    return {
        "destinationAndSourceUriMappingsList": destination_and_source_uri_mappings_list
    }
