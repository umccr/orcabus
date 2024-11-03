#!/usr/bin/env python3

"""
Lambda to determine if a given ICAv2 Copy Job has finished.
Returns the status of the job which is one of the following
* INITIALIZED
* WAITING_FOR_RESOURCES
* RUNNING
* STOPPED
* SUCCEEDED
* PARTIALLY_SUCCEEDED
* FAILED

The event input is
{
    "dest_uri": "icav2://path/to/destination/folder/"
    "source_uris": [
        "icav2://path/to/data",
        "icav2://path/to/data2",
    ]
    "job_id": null  # Or the job id abcd-1234-efgh-5678
    "failed_job_list": []  # Empty list or list of failed jobs
    "job_status": One of RUNNING, SUCCEEDED or FAILED (not the same as the job states, we rerun)
    "wait_time_seconds": int  # Number of seconds to wait before checking the job status - we add 10 seconds each time we go through this loop
}

"""

# Standard imports
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List
from urllib.parse import urlunparse, urlparse
import boto3
from os import environ
import typing
import logging
import re

# Wrapica imports
from wrapica.libica_models import ProjectData
from wrapica.job import get_job
from wrapica.enums import ProjectDataStatusValues, DataType
from wrapica.project_data import (
    convert_uri_to_project_data_obj, project_data_copy_batch_handler,
    delete_project_data,
    list_project_data_non_recursively,
    write_icav2_file_contents, read_icav2_file_contents,
    get_project_data_obj_from_project_id_and_path,
)

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Set logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)

# Globals
SUCCESS_STATES = [
    "SUCCEEDED"
]
TERMINAL_STATES = [
    "STOPPED",
    "FAILED",
    "PARTIALLY_SUCCEEDED"
]
RUNNING_STATES = [
    "INITIALIZED",
    "WAITING_FOR_RESOURCES",
    "RUNNING"
]

TINY_FILE_SIZE_LIMIT = 8388608  # 8 MiB (8 * 2^20)
MULTI_PART_ETAG_REGEX = re.compile(r"\w+-\d+")

# Try a job 10 times before giving up
MAX_JOB_ATTEMPT_COUNTER = 10
DEFAULT_WAIT_TIME_SECONDS = 10
DEFAULT_WAIT_TIME_SECONDS_EXT = 10

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


# AWS things
def get_ssm_client() -> 'SSMClient':
    """
    Return SSM client
    """
    return boto3.client("ssm")


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_ssm_parameter_value(parameter_path) -> str:
    """
    Get the ssm parameter value from the parameter path
    :param parameter_path:
    :return:
    """
    return get_ssm_client().get_parameter(Name=parameter_path)["Parameter"]["Value"]


def get_secret(secret_arn: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_arn)["SecretString"]


# Set the icav2 environment variables
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def tiny_file_transfer(dest_folder_project_data: ProjectData, source_file_project_data: ProjectData):
    """
    For tiny files (that have aws s3 tagging), ICAv2 cannot transfer these
    through jobs due to permission errors
    :param dest_folder_project_data:
    :param source_file_project_data:
    :return:
    """
    # Check file does not exist
    try:
        get_project_data_obj_from_project_id_and_path(
            project_id=dest_folder_project_data.project_id,
            data_path=Path(dest_folder_project_data.data.details.path) / source_file_project_data.data.details.name,
            data_type=DataType.FILE
        )
    except FileNotFoundError:
        pass
    else:
        # File already exists, no need to rerun
        return None

    # Download / upload tiny files
    with NamedTemporaryFile() as temp_file_obj:
        # Pull down data
        read_icav2_file_contents(
            source_file_project_data.project_id,
            source_file_project_data.data.id,
            Path(temp_file_obj.name)
        )
        # Write file contents
        write_icav2_file_contents(
            project_id=dest_folder_project_data.project_id,
            data_path=Path(dest_folder_project_data.data.details.path) / source_file_project_data.data.details.name,
            file_stream_or_path=Path(temp_file_obj.name)
        )

        # Get new file object
        dest_file_project_data_obj = get_project_data_obj_from_project_id_and_path(
            project_id=dest_folder_project_data.project_id,
            data_path=Path(dest_folder_project_data.data.details.path) / source_file_project_data.data.details.name,
            data_type=DataType.FILE
        )

        # Append ilmn tags from old file to new file
        # FIXME


def submit_copy_job(dest_project_data_obj: ProjectData, source_project_data_objs: List[ProjectData]) -> str:
    # Rerun copy batch process
    source_data_ids = list(
        map(
            lambda source_project_data_obj_iter_: source_project_data_obj_iter_.data.id,
            source_project_data_objs
        )
    )

    return project_data_copy_batch_handler(
        source_data_ids=source_data_ids,
        destination_project_id=dest_project_data_obj.project_id,
        destination_folder_path=Path(dest_project_data_obj.data.details.path)
    ).id


def delete_existing_partial_data(dest_project_data_obj: ProjectData):
    # Check list of files in the dest project data object and make sure no file has a partial status
    existing_files = list_project_data_non_recursively(
        dest_project_data_obj.project_id,
        dest_project_data_obj.data.id
    )

    for existing_file in existing_files:
        # Delete files with a 'partial' status
        if ProjectDataStatusValues(existing_file.data.details.status) == ProjectDataStatusValues.PARTIAL:
            logger.info(f"Deleting file {existing_file.data.details.path}, with 'partial' status before rerunning job")
            delete_project_data(
                existing_file.project_id,
                existing_file.data.id
            )


def get_source_uris_as_project_data_objs(source_uris: List[str]) -> List[ProjectData]:
    # Get source uris as project data objects
    return list(
        map(
            lambda source_uri_iter: convert_uri_to_project_data_obj(
                source_uri_iter
            ),
            source_uris
        )
    )


def filter_tiny_files_from_source_project_data_objs(
        source_project_data_objs: List[ProjectData],
        dest_folder_obj: ProjectData
) -> List[ProjectData]:
    source_project_data_list_filtered: List[ProjectData] = []
    for source_project_data_obj in source_project_data_objs:
        # Put all the big files into the job
        if (
            source_project_data_obj.data.details.file_size_in_bytes >= TINY_FILE_SIZE_LIMIT and
            MULTI_PART_ETAG_REGEX.fullmatch(source_project_data_obj.data.details.object_e_tag) is not None
        ):
            source_project_data_list_filtered.append(source_project_data_obj)
            continue
        # We have a tiny file, transfer via download + upload
        logger.info(
            f"File {source_project_data_obj.data.id} is too small to transfer via a job, "
            f"transferring via download+upload"
        )
        tiny_file_transfer(
            dest_folder_obj,
            source_project_data_obj
        )
    return source_project_data_list_filtered


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    # Get events
    dest_uri = event.get("dest_uri")
    source_uris = event.get("source_uris")
    job_id = event.get("job_id")
    failed_job_list = event.get("failed_job_list")
    wait_time_seconds = event.get("wait_time_seconds")

    # Get destination uri as project data object
    logger.info("Get dest project data folder object, create if it doesn't exist")
    dest_project_data_obj = convert_uri_to_project_data_obj(
        dest_uri,
        create_data_if_not_found=True
    )

    # Check if job is None
    if job_id is None:
        logger.info("First time, though delete any existing partial data")
        # First time through
        delete_existing_partial_data(dest_project_data_obj)

        # Get Source Uris as project data objects
        # Filter out files smaller than the min file size limit
        # These are transferred over manually
        source_project_data_list = filter_tiny_files_from_source_project_data_objs(
            get_source_uris_as_project_data_objs(source_uris),
            dest_project_data_obj
        )

        # Check we have a job to run
        if len(source_project_data_list) == 0:
            logger.info(f"No file larger than {TINY_FILE_SIZE_LIMIT} in size, no job to run")
            return {
                "dest_uri": dest_uri,
                "source_uris": source_uris,
                "job_id": None,
                "failed_job_list": [],  # Empty list or list of failed jobs
                "job_status": "SUCCEEDED",
                "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
            }

        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": submit_copy_job(
                dest_project_data_obj=dest_project_data_obj,
                source_project_data_objs=source_project_data_list,
            ),
            "failed_job_list": [],  # Empty list or list of failed jobs
            "job_status": "RUNNING",
            "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
        }

    # Else job id is not none
    job_obj = get_job(job_id)

    # Check job status

    # Return status
    if job_obj.status in SUCCESS_STATES:
        job_status = True
    elif job_obj.status in TERMINAL_STATES:
        job_status = False
    elif job_obj.status in RUNNING_STATES:
        job_status = None
    else:
        raise Exception("Unknown job status: {}".format(job_obj.status))

    # Check if we're still running
    if job_status is None:
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": job_id,
            # Empty list or list of failed jobs
            "failed_job_list": failed_job_list,
            "job_status": "RUNNING",
            # Wait a bit longer (an extra 10 seconds)
            "wait_time_seconds": wait_time_seconds + DEFAULT_WAIT_TIME_SECONDS_EXT
        }

    # Handle a failed job
    if job_status is False:
        # Add this job id to the failed job list
        failed_job_list.append(job_id)
        logger.warning(f"job id '{job_id}' failed with status {job_obj.status}")

        # Check we haven't exceeded the excess number of attempts
        if len(failed_job_list) >= MAX_JOB_ATTEMPT_COUNTER:
            # Most important bit is that the job_status is set to failed
            return {
                "dest_uri": dest_uri,
                "source_uris": source_uris,
                "job_id": None,
                "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
                "job_status": "FAILED",
                "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
            }

        # Return a new job with new wait time
        source_project_data_list = filter_tiny_files_from_source_project_data_objs(
            get_source_uris_as_project_data_objs(source_uris),
            dest_project_data_obj
        )
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": submit_copy_job(
                dest_project_data_obj=dest_project_data_obj,
                source_project_data_objs=source_project_data_list,
            ),
            "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
            "job_status": "RUNNING",
            "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
        }

    # Handle successful job
    if job_status is True:
        # Confirm source uris have made it to the destination successfully
        # Get dest folder
        dest_project_folder_data_obj: ProjectData = convert_uri_to_project_data_obj(dest_uri)

        # Iterate through each source uri
        has_errors = False
        for source_uri in source_uris:
            # Get the source project data object
            source_project_data_obj: ProjectData = convert_uri_to_project_data_obj(source_uri)

            # Get the dest uri file name
            dest_file_uri = str(
                urlunparse(
                    (
                        urlparse(dest_uri).scheme,
                        urlparse(dest_uri).netloc,
                        str(Path(urlparse(dest_uri).path) / source_project_data_obj.data.details.name),
                        None, None, None
                    )
                )
            )
            # Get the dest project data object
            dest_project_data_file_obj = convert_uri_to_project_data_obj(
                dest_file_uri
            )

            # Compare the source and dest project data objects etags
            if source_project_data_obj.data.details.file_size_in_bytes != dest_project_data_file_obj.data.details.file_size_in_bytes:
                # Set has errors to true
                has_errors = True
                logger.error("Data size mismatch between source and dest project data objects")
                logger.error(f"Data {source_uri} was transferred to {dest_file_uri} but the file sizes do not match")
                logger.error(f"Source file size: {source_project_data_obj.data.details.file_size_in_bytes}")
                logger.error(f"Dest file size: {dest_project_data_file_obj.data.details.file_size_in_bytes}")
                logger.error("Purging the dest uri file and starting again")
                # Purge the dest uri file and start again
                delete_project_data(
                    project_id=dest_project_data_file_obj.project_id,
                    data_id=dest_project_data_file_obj.data.id
                )

        # If we have errors, we need to rerun the job
        if has_errors:
            # Add this job id to the failed job list
            failed_job_list.append(job_id)

            # Delete any existing partial data
            delete_existing_partial_data(dest_project_data_obj)

            # Get source project data list uris
            source_project_data_list = filter_tiny_files_from_source_project_data_objs(
                get_source_uris_as_project_data_objs(source_uris),
                dest_project_data_obj
            )

            # Resubmit job
            return {
                "dest_uri": dest_uri,
                "source_uris": source_uris,
                "job_id": submit_copy_job(
                    dest_project_data_obj=dest_project_data_obj,
                    source_project_data_objs=source_project_data_list,
                ),
                "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
                "job_status": "RUNNING",
                "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
            }

        # If we don't have errors, we can return the job as successful
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": job_id,
            "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
            "job_status": "SUCCEEDED",
            "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
        }


# Just Small files
# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = 'ICAv2JWTKey-umccr-prod-service-dev'
#     print(
#         json.dumps(
#             handler(
#                 event={
#                 "job_id": None,
#                 "failed_job_list": [],
#                 "wait_time_seconds": 5,
#                 "job_status": None,
#                 "dest_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/cache/cttsov2/20241031d8a13553/L2401532/",
#                 "source_uris": [
#                     "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401532/L2401532_S7_L001_R1_001.fastq.gz",
#                     "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401532/L2401532_S7_L001_R2_001.fastq.gz"
#                 ],
#               },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "dest_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/cache/cttsov2/20241031d8a13553/L2401532/",
#     #     "source_uris": [
#     #         "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401532/L2401532_S7_L001_R1_001.fastq.gz",
#     #         "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401532/L2401532_S7_L001_R2_001.fastq.gz"
#     #     ],
#     #     "job_id": null,
#     #     "failed_job_list": [],
#     #     "job_status": "SUCCEEDED",
#     #     "wait_time_seconds": 10
#     # }


# Copy files with mixed small and large
# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = 'ICAv2JWTKey-umccr-prod-service-dev'
#     print(
#         json.dumps(
#             handler(
#                 event={
#                 "job_id": None,
#                 "failed_job_list": [],
#                 "wait_time_seconds": 5,
#                 "job_status": None,
#                 "dest_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/cache/cttsov2/20241031d8a13553/small-files-copy-test/",
#                 "source_uris": [
#                     "icav2://development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/small-files/chunk_file_size_8mb.bin",
#                     "icav2://development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/small-files/chunk_file_size_8mb_minus_1.bin"
#                 ],
#               },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "dest_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/cache/cttsov2/20241031d8a13553/L2401532/",
#     #     "source_uris": [
#     #         "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401532/L2401532_S7_L001_R1_001.fastq.gz",
#     #         "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_1/L2401532/L2401532_S7_L001_R2_001.fastq.gz"
#     #     ],
#     #     "job_id": null,
#     #     "failed_job_list": [],
#     #     "job_status": "SUCCEEDED",
#     #     "wait_time_seconds": 10
#     # }
