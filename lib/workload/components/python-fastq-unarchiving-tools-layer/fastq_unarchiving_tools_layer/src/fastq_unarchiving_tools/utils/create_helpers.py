#!/usr/bin/env python3

"""
Create the job
"""

from typing import List, Optional
from .request_helpers import post_request
from .globals import FASTQ_UNARCHIVING_SUBDOMAIN_NAME
from .models import Job, JobType


def create_job(fastq_ids: List[str], job_type: Optional[JobType] = None) -> Job:
    """
    Create the job
    """
    if job_type is None:
        job_type = JobType.S3_UNARCHIVING

    return post_request(
        FASTQ_UNARCHIVING_SUBDOMAIN_NAME,
        params={
            "fastqIds": fastq_ids,
            "jobType": job_type.value
        }
    )
