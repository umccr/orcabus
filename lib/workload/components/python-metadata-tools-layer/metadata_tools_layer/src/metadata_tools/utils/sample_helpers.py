#!/usr/bin/env python3


# !/usr/bin/env python3


"""
Helper functions for a subject
"""

# Standard imports
from typing import List, Union, Dict

# Local imports
from .globals import SAMPLE_ENDPOINT, LIBRARY_ENDPOINT
from .requests_helpers import get_request_response_results


def get_sample_from_sample_id(sample_id: str) -> Dict:
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
    return get_request_response_results(SAMPLE_ENDPOINT, params)[0]


def get_sample_from_sample_orcabus_id(sample_orcabus_id: str) -> Dict:
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
    return get_request_response_results(SAMPLE_ENDPOINT, params)[0]



def list_libraries_in_sample(sample_id: Union[str, int]) -> List[Dict]:
    """
    Given a sample_id, list the samples in the subject
    :param sample_id:
    :return:
    """
    # Get the subject
    return list(
        filter(
            lambda library_iter: library_iter.get("sample").get("sampleId") == sample_id,
            get_request_response_results(LIBRARY_ENDPOINT)
        )
    )


def get_all_samples():
    """
    Get all samples from the sample database
    :return:
    """
    return get_request_response_results(SAMPLE_ENDPOINT)
