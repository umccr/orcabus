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
import boto3
from os import environ
import typing

# Wrapica imports
from wrapica.job import get_job
from wrapica.project_data import (
    convert_uri_to_project_data_obj, project_data_copy_batch_handler
)

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

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
            "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
            "job_status": "RUNNING",
            "wait_time_seconds": wait_time_seconds + DEFAULT_WAIT_TIME_SECONDS_EXT # Wait a bit longer (an extra 10 seconds)
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
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = 'ICAv2JWTKey-umccr-prod-service-trial'
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "job_attempt_counter": 1,
#                     "job_id": "d80ea8f4-b2a4-4b5f-840f-2426584d0495",
#                     "failed_jobs_list": [],
#                     "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/InterOp/",
#                     "source_uris": [
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/AlignmentMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/EmpiricalPhasingMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/CorrectedIntMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/BasecallingMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ErrorMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ExtendedTileMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/OpticalModelMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetricsByLaneOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ExtractionMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/PFGridMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ImageMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/TileMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetrics2030Out.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/FWHMGridMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/EventMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/RegistrationMetricsOut.bin",
#                         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/IndexMetricsOut.bin"
#                     ],
#                     "job_status": None,
#                     "wait_time_seconds": 10
#                 },
#                 context=None
#             )
#         )
#     )

