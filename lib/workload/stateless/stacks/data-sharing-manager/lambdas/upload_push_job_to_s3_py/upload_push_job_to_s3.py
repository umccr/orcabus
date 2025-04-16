#!/usr/bin/env python3

"""
Upload push job to s3:

This is for archiving purposes. We need to save push jobs to s3 so that if we need to one day review what was pushed, we can do so.

This involves:
1. Querying the entire content index for a packaging job.
  * Metadata
  * Fastq
  * Workflow
  * Files

2. Get the share destination, packaging id, and push job id (from the inputs)

3. Storing this into a giant parquet file

3. Uploading the parquet file to s3
"""
import typing
from urllib.parse import urlparse

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

import boto3
from pathlib import Path

from pyarrow import LargeStringScalar

from data_sharing_tools.utils.dynamodb_helpers import query_dynamodb_table
from data_sharing_tools.utils.update_helpers import get_push_job_from_steps_execution_id
from datetime import datetime
from tempfile import TemporaryDirectory

from typing import TypedDict, Dict, List, Union, Tuple, Hashable, Any

if typing.TYPE_CHECKING:

    from mypy_boto3_s3 import S3Client

    class PackageJobData(TypedDict):
        library: pd.DataFrame
        fastq: pd.DataFrame
        workflow: pd.DataFrame
        file: pd.DataFrame


    class PushJobData(TypedDict):
        """
        Push job data
        """
        push_job_id: str
        packaging_job_id: str
        share_destination: LargeStringScalar
        share_date: datetime
        package: PackageJobData


def get_s3_client() -> 'S3Client':
    return boto3.client('s3')


def get_bucket_key_tuple_from_uri(uri: str) -> Tuple[str, str]:
    url_obj = urlparse(uri)

    return url_obj.netloc, url_obj.path.lstrip('/')


def get_data(packaging_job_id, context) -> Dict[
    str,
    List[Dict[Hashable, Any]]
]:
    # Get the library information
    return {
        # Library information
        "library": pd.DataFrame(query_dynamodb_table(
            job_id=packaging_job_id,
            context="library"
        )).to_dict(orient='records'),
        # Get the fastq information
        "fastq": pd.DataFrame(query_dynamodb_table(
            job_id=packaging_job_id,
            context="fastq"
        )).to_dict(orient='records'),
        # Get the workflow information
        "workflow": pd.DataFrame(query_dynamodb_table(
            job_id=packaging_job_id,
            context="workflow"
        )).to_dict(orient='records'),
        # Get the files information
        "files": pd.DataFrame(query_dynamodb_table(
            job_id=packaging_job_id,
            context="files"
        )).to_dict(orient='records')
    }


def handler(event, context):
    """
    Get the inputs

    1. packaging job id
    2. the share destination
    3. Get the push id by querying the execution id
    4. Get the all the attributes by pulling into the content index
    :param event:
    :param context:
    :return:
    """

    # Get inputs
    packaging_job_id = event.get("packagingJobId")
    share_destination = event.get("shareDestination")
    push_execution_arn = event.get("pushExecutionArn")

    # Get the push job id by querying the execution id
    push_job_obj = get_push_job_from_steps_execution_id(
        push_execution_arn,
        package_job_id=packaging_job_id
    )

    # Get the push job object attributes
    push_job_id = push_job_obj.get("id")
    share_date = push_job_obj.get("startTime")
    output_uri = push_job_obj.get("logUri")

    # Create the table
    push_data = pd.DataFrame(
        [
            {
                "push_job_id": push_job_id,
                "packaging_job_id": packaging_job_id,
                "share_destination": share_destination,
                "share_date": share_date,
                "package": get_data(
                    packaging_job_id=packaging_job_id,
                    context=context
                )
            }
        ]
    )

    table = pa.Table.from_pandas(push_data)

    # Get the temp directory object
    temp_dir = Path(TemporaryDirectory(delete=False).name)
    output_path = temp_dir / f'{push_job_id}.parquet'

    pq.write_table(
        table,
        output_path
    )

    # Upload the parquet file to s3
    bucket, key = get_bucket_key_tuple_from_uri(output_uri)
    get_s3_client().upload_file(
        Filename=str(output_path),
        Bucket=bucket,
        Key=key
    )


# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     # Set env vars
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['PACKAGING_TABLE_NAME'] = 'data-sharing-packaging-lookup-table'
#     environ['CONTENT_INDEX_NAME'] = 'content-index'
#
#     print(json.dumps(
#         handler(
#             {
#                 "packagingJobId": "pkg.01JQYYBM52ZDYZ5MFMX7C22QHS",
#                 "shareDestination": "s3://umccr-test-destination-prod/L2301542-outputs-fastq-test-2/",
#                 "pushExecutionArn": "arn:aws:states:ap-southeast-2:472057503814:execution:data-sharing-push-parent-sfn:89aec633-42d3-46e3-a990-153c507d6ba8"
#             },
#             None
#         ),
#         indent=4
#     ))