#!/usr/bin/env python3

"""
Query helpers -

get_job_from_job_id

get_unarchiving_job_list

"""
from typing import List

from .models import Job
from .request_helpers import (
    get_request_response_results,
)

from .globals import JOB_ENDPOINT


def get_job_from_job_id(job_id: str, **kwargs) -> Job:
    return get_request_response_results(f"{JOB_ENDPOINT}/{job_id}", params=kwargs)


def get_unarchiving_job_list(*args, **kwargs) -> List[Job]:
    """
    Get all fastqs
    """
    return get_request_response_results(JOB_ENDPOINT, params=kwargs)

