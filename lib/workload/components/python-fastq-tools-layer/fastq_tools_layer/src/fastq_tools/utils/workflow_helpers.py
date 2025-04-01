#!/usr/bin/env python3

"""
Workflow helpers - a collection of helper functions for the workflow

- to_cwl: Given a fastq id, convert to a cwl file
"""


# Local imports
from .models import CWLDict
from .globals import FASTQ_LIST_ROW_ENDPOINT
from .request_helpers import get_request_response_results


def to_cwl(fastq_id) -> CWLDict:
    return get_request_response_results(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/toCwl"
    )
