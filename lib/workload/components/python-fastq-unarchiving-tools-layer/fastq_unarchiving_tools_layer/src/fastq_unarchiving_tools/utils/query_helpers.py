#!/usr/bin/env python3

"""
Query helpers -

get_job_from_job_id

get_unarchiving_job_list

"""
from typing import List

from .request_helpers import (
    get_request_response_results,
)

from .globals import FASTQ_LIST_ROW_ENDPOINT, FASTQ_SET_ENDPOINT
from .models import FastqListRow, FastqSet


def get_job_from_job_id(job_id: str, **kwargs) -> FastqListRow:
    return get_request_response_results(f"{FASTQ_LIST_ROW_ENDPOINT}/{job_id}", params=kwargs)


def get_unarchiving_job_list(*args, **kwargs) -> List[FastqListRow]:
    """
    Get all fastqs
    """
    return get_request_response_results(FASTQ_LIST_ROW_ENDPOINT, params=kwargs)

