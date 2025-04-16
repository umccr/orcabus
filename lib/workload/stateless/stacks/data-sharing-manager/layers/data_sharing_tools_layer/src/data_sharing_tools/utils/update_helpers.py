#!/usr/bin/env python3

"""
Update helpers for the update script.

"""

# Standard imports
from typing import Optional

# Local imports
from .globals import JobStatus, PACKAGING_ENDPOINT, PUSH_JOB_ENDPOINT
from .request_helpers import patch_request, get_request_response_results
from .models import PackageResponseDict, PushJobResponseDict


def update_package_status(job_id: str, job_status: JobStatus, error_message: Optional[str] = None) -> PackageResponseDict:
    """
    Add a status to the package job.

    :param job_id: Job Id
    :param job_status: Job Status
    :param error_message: Error message
    """
    return patch_request(
        f"{PACKAGING_ENDPOINT}/{job_id}",
        params=dict(filter(
            lambda x: x[1] is not None,
            {
                "status": job_status.value,
                "errorMessage": error_message
            }.items()
        ))
    )


def get_push_job_from_steps_execution_id(steps_execution_id: str, package_job_id: Optional[str] = None) -> PushJobResponseDict:
    return next(filter(
        lambda push_job_iter_: push_job_iter_["stepFunctionsExecutionArn"] == steps_execution_id,
        get_request_response_results(
            PUSH_JOB_ENDPOINT,
            params=dict(filter(
                lambda kv: kv[1] is not None,
                {
                    "packageId": package_job_id
                }.items()
            ))
        )
    ))


def update_push_job_status_from_steps_execution_id(
        steps_execution_id: str,
        job_status: JobStatus,
        error_message: Optional[str] = None,
        package_job_id: Optional[str] = None,
) -> PushJobResponseDict:
    return update_push_job_status(
        get_push_job_from_steps_execution_id(steps_execution_id, package_job_id=package_job_id)["id"],
        job_status,
        error_message
    )


def update_push_job_status(job_id: str, job_status: JobStatus, error_message: Optional[str] = None) -> PushJobResponseDict:
    return patch_request(
        f"{PUSH_JOB_ENDPOINT}/{job_id}",
        params=dict(filter(
            lambda x: x[1] is not None,
            {
                "status": job_status,
                "errorMessage": error_message
            }.items()
        ))
    )

