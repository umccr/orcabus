#!/usr/bin/env python3


# !/usr/bin/env python3


"""
Helper functions for a subject
"""

# Standard imports
from typing import List, Dict

# Local imports
from .errors import SampleNotFoundError
from .globals import SAMPLE_ENDPOINT
from requests.exceptions import HTTPError

from .models import Sample, LibraryDetail
from .requests_helpers import get_request_response_results


def get_sample_from_sample_id(sample_id: str) -> Sample:
    """
    Get sample from the sample id
    :param sample_id:
    :return:
    """
    # We have an internal id
    params = {
        "sample_id": sample_id
    }

    # Get sample
    try:
        query_results = get_request_response_results(SAMPLE_ENDPOINT, params)
        assert len(query_results) == 1
        return query_results[0]
    except (HTTPError, AssertionError):
        raise SampleNotFoundError(
            sample_id=sample_id
        )


def get_sample_orcabus_id_from_sample_id(sample_id: str) -> str:
    return get_sample_from_sample_id(sample_id)["orcabusId"]


def get_sample_from_sample_orcabus_id(sample_orcabus_id: str) -> Sample:
    """
    Get sample from the sample id
    :param sample_orcabus_id:
    :return:
    """
    # We have an internal id
    params = {
        "orcabus_id": sample_orcabus_id
    }

    # Get sample
    try:
        query_results = get_request_response_results(SAMPLE_ENDPOINT, params)
        assert len(query_results) == 1
    except (HTTPError, AssertionError):
        raise SampleNotFoundError(
            sample_orcabus_id=sample_orcabus_id
        )


def list_libraries_in_sample(sample_orcabus_id: str) -> List[LibraryDetail]:
    """
    Given a sample id, return the list of library objects in the sample
    :param sample_orcabus_id:
    :return:
    """
    # Get ID For Subject
    sample = get_sample_from_sample_orcabus_id(sample_orcabus_id)

    # Get the sample
    return sample.get("librarySet", [])


def get_all_samples():
    """
    Get all samples from the sample database
    :return:
    """
    return get_request_response_results(SAMPLE_ENDPOINT)
