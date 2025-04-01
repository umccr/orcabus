#!/usr/bin/env python3

"""
Update helpers for the update script.

- run_qc_stats
- run_ntsm
- run_file_compression_information
"""

# Standard imports

# Local imports
from .globals import FASTQ_LIST_ROW_ENDPOINT
from .request_helpers import patch_request
from .models import Job


def run_qc_stats(fastq_id) -> Job:
    """
    Add QC stats to a fastq_id.

    :param fastq_id: Fastq str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}:runQcStats",
    )


def run_ntsm(fastq_id) -> Job:
    """
    Run ntsm for a fastq_id.

    :param fastq_id: Fastq str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}:runNtsm",
    )


def run_file_compression_stats(fastq_id) -> Job:
    """
    Run file compression stats for a fastq_id.

    :param fastq_id: Fastq str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}:runFileCompressionInformation",
    )

