#!/usr/bin/env python3

"""
Given a list of file objects, generate a csv (per portal run id) that comprises bucket,key prefixes
"""

# Imports
from os import environ
from typing import List
import pandas as pd

# Layer imports
from data_sharing_tools import upload_str_to_s3
from filemanager_tools import (
    FileObject, get_restore_prefix_from_account_id, get_cache_bucket_from_account_id
)

# Globals
S3_STEPS_CSV_UPLOAD_BUCKET_ENV_VAR = "S3_STEPS_CSV_UPLOAD_BUCKET"
S3_STEPS_CSV_UPLOAD_PREFIX_ENV_VAR = "S3_STEPS_CSV_UPLOAD_PREFIX"


def handler(event, context):
    """
    Upload archive file list as csv
    :param event:
    :param context:
    :return:
    """
    # Get the list of file objects
    archived_file_list: List['FileObject'] = event.get('archivedFileList', None)
    steps_execution_id: str = event.get('steps_execution_id', None)

    if not archived_file_list:
        raise ValueError('No archived file list provided')

    # Check environment variables are not empty
    s3_steps_csv_upload_bucket = environ.get(S3_STEPS_CSV_UPLOAD_BUCKET_ENV_VAR)
    if not environ.get(S3_STEPS_CSV_UPLOAD_BUCKET_ENV_VAR):
        raise ValueError(f"Environment variable {S3_STEPS_CSV_UPLOAD_BUCKET_ENV_VAR} not set")
    s3_steps_csv_upload_prefix = environ.get(S3_STEPS_CSV_UPLOAD_PREFIX_ENV_VAR)
    if not environ.get(S3_STEPS_CSV_UPLOAD_PREFIX_ENV_VAR):
        raise ValueError(f"Environment variable {S3_STEPS_CSV_UPLOAD_PREFIX_ENV_VAR} not set")

    # Generate the csv
    df = pd.DataFrame(archived_file_list)

    # Get the portal run id for each object from the attributes
    df['portalRunId'] = df['attributes'].apply(lambda x: x['portalRunId'])

    # Group by portal run id and concatenate the bucket and key
    csv_uris = []
    dest_paths = []
    for portal_run_id, portal_run_df in df.groupby('portalRunId'):
        csv_str = portal_run_df[['bucket', 'key']].to_csv(index=False, header=False)
        upload_key = f"{s3_steps_csv_upload_prefix}/{steps_execution_id}/{portal_run_id}.csv"

        # Upload the s3 file
        upload_str_to_s3(csv_str, s3_steps_csv_upload_bucket, upload_key)

        # Append the key
        csv_uris.append(f"s3://{s3_steps_csv_upload_bucket}/{upload_key}")

        # Append the destination path
        dest_paths.append(
            f"s3://{get_cache_bucket_from_account_id}/{get_restore_prefix_from_account_id()}{steps_execution_id}/{portal_run_id}/"
        )

    return {
        'csvList': csv_uris,
        'destPaths': dest_paths,
    }
