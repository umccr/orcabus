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
from typing import List
from urllib.parse import urlunparse, urlparse
import boto3
from os import environ
import typing
import logging

# Wrapica imports
from wrapica.libica_models import ProjectData
from wrapica.job import get_job
from wrapica.project_data import (
    convert_uri_to_project_data_obj, project_data_copy_batch_handler, delete_project_data
)

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def submit_copy_job(dest_uri: str, source_uris: List[str]) -> str:
    # Rerun copy batch process
    source_data_ids = list(
        map(
            lambda source_uri_iter: convert_uri_to_project_data_obj(
                source_uri_iter
            ).data.id,
            source_uris
        )
    )

    dest_project_data_obj = convert_uri_to_project_data_obj(
        dest_uri,
        create_data_if_not_found=True
    )

    return project_data_copy_batch_handler(
        source_data_ids=source_data_ids,
        destination_project_id=dest_project_data_obj.project_id,
        destination_folder_path=Path(dest_project_data_obj.data.details.path)
    ).id


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
    job_status = event.get("job_status")
    wait_time_seconds = event.get("wait_time_seconds")

    # Check if job is None
    if job_id is None:
        # First time through
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": submit_copy_job(
                dest_uri=dest_uri,
                source_uris=source_uris,
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
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": submit_copy_job(
                dest_uri=dest_uri,
                source_uris=source_uris,
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
            return {
                "dest_uri": dest_uri,
                "source_uris": source_uris,
                "job_id": submit_copy_job(
                    dest_uri=dest_uri,
                    source_uris=source_uris,
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


# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = 'ICAv2JWTKey-umccr-prod-service-production'
#     print(
#         json.dumps(
#             handler(
#                 event={
#                 "job_status": "RUNNING",
#                 "wait_time_seconds": 20,
#                 "job_id": "bdfb0a4d-bcae-4670-b51f-9417d23e777a",
#                 "dest_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/240926_A01052_0232_AHW7LHDSXC/20240928f63332ac/Samples/Lane_4/LPRJ241305/",
#                 "source_uris": [
#                   "icav2://9ec02c1f-53ba-47a5-854d-e6b53101adb7/ilmn-analyses/240926_A01052_0232_AHW7LHDSXC_f5e33a_03217c-BclConvert v4_2_7-792cba71-52fa-42b3-85a0-c6593f199353/output/Samples/Lane_4/LPRJ241305/LPRJ241305_S41_L004_R1_001.fastq.gz",
#                   "icav2://9ec02c1f-53ba-47a5-854d-e6b53101adb7/ilmn-analyses/240926_A01052_0232_AHW7LHDSXC_f5e33a_03217c-BclConvert v4_2_7-792cba71-52fa-42b3-85a0-c6593f199353/output/Samples/Lane_4/LPRJ241305/LPRJ241305_S41_L004_R2_001.fastq.gz"
#                 ],
#                 "failed_job_list": []
#               },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
# # {
# #     "dest_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/240926_A01052_0232_AHW7LHDSXC/20240928f63332ac/Samples/Lane_4/LPRJ241305/",
# #     "source_uris": [
# #         "icav2://9ec02c1f-53ba-47a5-854d-e6b53101adb7/ilmn-analyses/240926_A01052_0232_AHW7LHDSXC_f5e33a_03217c-BclConvert v4_2_7-792cba71-52fa-42b3-85a0-c6593f199353/output/Samples/Lane_4/LPRJ241305/LPRJ241305_S41_L004_R1_001.fastq.gz",
# #         "icav2://9ec02c1f-53ba-47a5-854d-e6b53101adb7/ilmn-analyses/240926_A01052_0232_AHW7LHDSXC_f5e33a_03217c-BclConvert v4_2_7-792cba71-52fa-42b3-85a0-c6593f199353/output/Samples/Lane_4/LPRJ241305/LPRJ241305_S41_L004_R2_001.fastq.gz"
# #     ],
# #     "job_id": "bdfb0a4d-bcae-4670-b51f-9417d23e777a",
# #     "failed_job_list": [],
# #     "job_status": "SUCCEEDED",
# #     "wait_time_seconds": 10
# # }
