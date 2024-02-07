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
    "job_id": "12345"
}

"""
from bssh_manager_tools.utils.icav2_configuration_helper import set_icav2_env_vars
from bssh_manager_tools.utils.icav2_job_handler import get_job

SUCCESS_STATES = [
    "SUCCEEDED"
]
TERMINAL_STATES = [
    "STOPPED",
    "FAILED"
]
RUNNING_STATES = [
    "INITIALIZED",
    "WAITING_FOR_RESOURCES",
    "RUNNING"
]


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """

    # Import env vars
    set_icav2_env_vars()

    # Get job object
    job = get_job(event.get("job_id"))

    # Return status
    if job.status in SUCCESS_STATES:
        return True
    elif job.status in TERMINAL_STATES:
        return False
    elif job.status in RUNNING_STATES:
        return None
    else:
        raise Exception("Unknown job status: {}".format(job.status))


