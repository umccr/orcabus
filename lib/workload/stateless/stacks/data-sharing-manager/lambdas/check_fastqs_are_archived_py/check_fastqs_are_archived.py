#!/usr/bin/env python3

"""
SFN LAMBDA FUNCTION PLACEHOLDER: __check_fastqs_are_archived_lambda_function_arn__

Given a fastq object, check if the fastq files are archived.

# FIXME - currently perform this with a simply boolean, if in archive bucket, True else False,

# FIXME - I think this was written a while ago

# FIXME -

If in archive bucket, check for the presence of the files of the same name in the restored directory
"""
import re
from pathlib import Path
from typing import List
from filemanager_tools import (
    FileObject,
    file_search, get_cache_bucket_from_account_id,
    get_restore_prefix_from_account_id, get_archive_fastq_bucket_from_account_id
)
from data_sharing_tools import (
    read_in_s3_json_objects_as_list, upload_obj_to_s3,
    delete_s3_obj
)


def handler(event, context):
    """
    Determine if the fastq object is in the archive, if true, check the restore object for the presence of the files of the same name,
    Otherwise return False
    :param event:
    :param context:
    :return:
    """

    # Get bucket and prefix of the file objects
    bucket = event.get('bucket', None)
    prefix = event.get('prefix', None)

    # Ensure that the bucket and prefix are not None
    if bucket is None or prefix is None:
        raise ValueError("Bucket and prefix must be provided")

    # Get all the files in the bucket
    files_list: List[FileObject] = read_in_s3_json_objects_as_list(bucket, prefix)

    # For each file, check if it is in the archive
    any_archived = False
    archived_file_list = []
    for file_iter_ in files_list:
        # When we scan this folder, we may be simultaneously writing in secondary analysis file objects
        # Therefore we need to check if the file object is a fastq file first before we try to check if it is in the archive
        if (
                file_iter_['bucket'] == get_archive_fastq_bucket_from_account_id()
        ) and (
                re.match(file_iter_['key'], ".fastq.(?:gz|ora)$")
        ):
            # Check if the s3 uri has been restored
            # Find the equivalent sample in the restored bucket
            for restored_file in file_search(
                    bucket=get_cache_bucket_from_account_id(),
                    key=f"{get_restore_prefix_from_account_id()}*/{Path(file_iter_['key']).name}"
            ):
                if restored_file['attributes']['portalRunId'] == file_iter_['attributes']['portalRunId']:
                    # Delete s3ObjectId from the bucket list
                    delete_s3_obj(
                        bucket=bucket,
                        key=f"{prefix}{file_iter_['s3ObjectId']}.json"
                    )
                    # We upload this json object and replace the original
                    upload_obj_to_s3(
                        data=restored_file,
                        bucket=bucket,
                        key=f"{prefix}{file_iter_['s3ObjectId']}.json"
                    )
                    break
            else:
                # If the restored file is not found, then the file is not archived
                archived_file_list.append(file_iter_)
                any_archived = True

    return {
        "archivedFileList": archived_file_list,
        "anyArchived": any_archived
    }
