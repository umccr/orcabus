#!/usr/bin/env python3

"""
Update helpers for the update script.

- add_qc_stats
- add_read_count
- add_ntsm_storage_object / add_ntsm
- add_fastq_pair_storage_object / add_read_set
- detach_fastq_pair_storage_object / detach_read_set
- validate
- invalidate
"""

# Standard imports
from typing import Optional

# Local imports
from .globals import JobStatus, JOB_ENDPOINT
from .request_helpers import patch_request
from .models import Job


def update_status(job_id: str, job_status: JobStatus, error_message: Optional[str] = None) -> Job:
    """
    Add QC stats to a fastq_id.

    :param fastq_id: Fastq str
    :param qc_stats: Dictionary of QC stats
    """
    return patch_request(
        f"{JOB_ENDPOINT}/{job_id}",
        params=dict(filter(
            lambda x: x[1] is not None,
            {
                "status": job_status,
                "error_message": error_message
            }.items()
        ))
    )


