#!/usr/bin/env python3


"""
Helper functions for a subject
"""

# Standard imports
from typing import List, Union, Dict

# Local imports
from .requests_helpers import get_request_response_results


def get_subject_from_subject_id(subject_id: Union[str, int]) -> Dict:
    """
    Get subject from the subject id
    :param subject_id:
    :return:
    """
    endpoint = "api/v1/subject"

    # Get subject id
    if isinstance(subject_id, str):
        # We have an internal id, convert to int
        params = {
            "subject_id": subject_id
        }
    else:
        endpoint = f"{endpoint}/{subject_id}"
        params = {}

    # Get subject
    return get_request_response_results(endpoint, params)[0]


def list_specimens_in_subject(subject_id: Union[str, int]) -> List[Dict]:
    """
    Given a subject id, list the specimens in the subject
    :param subject_id:
    :return:
    """
    from metadata_tools import get_all_specimens

    # Get ID For Subject
    subject = get_subject_from_subject_id(subject_id)

    # Get the subject
    return list(
        filter(
            lambda specimen_iter:
            subject.get("id") == specimen_iter.get("subjects")[0] if "subjects" in specimen_iter.keys()
            else specimen_iter.get("subject") == subject.get("id"),
            get_all_specimens()
        )
    )


def list_libraries_in_subject(subject_id: str) -> List[Dict]:
    """
    Given a subject id, return the list of library objects in the subject
    :param subject_id:
    :return:
    """
    from .specimen_helpers import list_libraries_in_specimen

    library_list = []

    specimens_list = list_specimens_in_subject(subject_id)

    for specimen_iter in specimens_list:
        library_list.extend(list_libraries_in_specimen(specimen_iter.get("id")))

    return library_list


def get_all_subjects() -> List[Dict]:
    """
    Get all subjects
    :return:
    """

    endpoint = "api/v1/subject"

    return get_request_response_results(endpoint)
