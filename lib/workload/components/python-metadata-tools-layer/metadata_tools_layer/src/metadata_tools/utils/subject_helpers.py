#!/usr/bin/env python3


"""
Helper functions for a subject
"""

# Standard imports
from typing import List, Union, Dict

from .globals import SUBJECT_ENDPOINT
# Local imports
from .requests_helpers import get_request_response_results


def get_subject_from_subject_id(subject_id: str) -> Dict:
    """
    Get subject from the subject id
    :param subject_id:
    :return:
    """
    # We have an internal id, convert to int
    params = {
        "subject_id": subject_id
    }

    # Get subject
    return get_request_response_results(SUBJECT_ENDPOINT, params)[0]



def get_subject_from_subject_orcabus_id(subject_orcabus_id: str) -> Dict:
    """
    Get subject from the subject id
    :param subject_orcabus_id:
    :return:
    """
    # Get subject id
    # We have an internal id, convert to int
    params = {
        "orcabus_id": subject_orcabus_id
    }

    # Get subject
    return get_request_response_results(SUBJECT_ENDPOINT, params)[0]


def list_samples_in_subject(subject_id: Union[str, int]) -> List[Dict]:
    """
    Given a subject id, list the samples in the subject
    :param subject_id:
    :return:
    """
    from metadata_tools import get_all_samples

    # Get ID For Subject
    subject = get_subject_from_subject_id(subject_id)

    # Get the subject
    return list(
        filter(
            lambda sample_iter:
            subject.get("id") == sample_iter.get("subjects")[0]
            if "subjects" in sample_iter.keys()
            else
            sample_iter.get("subject") == subject.get("id"),
            get_all_samples()
        )
    )


def list_libraries_in_subject(subject_id: str) -> List[Dict]:
    """
    Given a subject id, return the list of library objects in the subject
    :param subject_id:
    :return:
    """
    from .sample_helpers import list_libraries_in_sample

    library_list = []

    samples_list = list_samples_in_subject(subject_id)

    for sample_iter in samples_list:
        library_list.extend(list_libraries_in_sample(sample_iter.get("id")))

    return library_list


def get_all_subjects() -> List[Dict]:
    """
    Get all subjects
    :return:
    """
    return get_request_response_results(SUBJECT_ENDPOINT)
