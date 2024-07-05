#!/usr/bin/env python3


# !/usr/bin/env python3


"""
Helper functions for a subject
"""

# Standard imports
from typing import List, Union, Dict

# Local imports
from .requests_helpers import get_request_response_results


def get_specimen_from_specimen_id(specimen_id: Union[str, int]) -> Dict:
    """
    Get specimen from the specimen id
    :param specimen_id:
    :return:
    """
    endpoint = "specimen"

    # Get specimen id
    if isinstance(specimen_id, str):
        # We have an internal id, convert to int
        params = {
            "internal_id": specimen_id
        }
    else:
        endpoint = f"{endpoint}/{specimen_id}"
        params = {}

    # Get specimen
    return get_request_response_results(endpoint, params)[0]


def list_libraries_in_specimen(specimen_id: Union[str, int]) -> List[Dict]:
    """
    Given a specimen_id id, list the specimens in the subject
    :param specimen_id:
    :return:
    """

    # If subject id is a string, we have the internal id (SBJ...)
    specimen = get_specimen_from_specimen_id(specimen_id)

    endpoint = f"library"

    # Get the subject
    return list(
        filter(
            lambda library_iter: library_iter.get("specimen") == specimen.get("id"),
            get_request_response_results(endpoint)
        )
    )


def get_all_specimens():
    """
    Get all specimens from the specimen database
    :return:
    """
    endpoint = "specimen"

    return get_request_response_results(endpoint)

