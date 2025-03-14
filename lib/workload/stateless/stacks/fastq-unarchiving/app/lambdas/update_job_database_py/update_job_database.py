#!/usr/bin/env python3

"""
Use the fastq unarchiving layer construct to update the job database with a job success event

We expect either a 'RUNNING' update

{
    "jobId": "string",
    "status": "RUNNING",
}

OR

{
    "jobId": "string",
    "hasError": false,
    "errorMessages": "",
    "status": "SUCCEEDED"
}

OR

{
    "jobId": "string",
    "hasError": true,
    "errorMessages": "string",
    "status": "FAILED"
}

"""

from fastq_unarchiving_tools import update_status


def handler(event, context):
    """
    Get inputs then use the fastq unarchiving tools layer to update the status of a job in the database
    :param event:
    :param context:
    :return:
    """
    # Get inputs
    job_id = event.get('jobId')
    status = event.get('status')
    has_error = event.get('hasError', False)

    if not has_error:
        return update_status(job_id, status)
    else:
        error_message = event.get('errorMessages', None)
        update_status(job_id, status, error_message)
