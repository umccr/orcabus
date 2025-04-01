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

# Local imports
from .globals import FASTQ_LIST_ROW_ENDPOINT, FASTQ_SET_ENDPOINT
from .request_helpers import post_request
from .models import FastqListRow, FastqSet, FastqListRowCreate, FastqSetCreate


def create_fastq_list_row_object(fastq_list_row_create_dict: FastqListRowCreate) -> FastqListRow:
    """
    Add a fastq list row object to the database.
    Returns the created fastq list row object
    """
    return post_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}",
        params=fastq_list_row_create_dict
    )


def create_fastq_set_object(fastq_set_create_dict: FastqSetCreate) -> FastqSet:
    """
    Add a fastq list row object to the database.
    Returns the created fastq list row object
    """
    return post_request(
        f"{FASTQ_SET_ENDPOINT}",
        params=fastq_set_create_dict
    )
