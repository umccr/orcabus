#!/usr/bin/env python3


"""
Helper functions for a subject
"""

# Standard imports
from typing import List
from requests import HTTPError

# Local imports
from .errors import SubjectNotFoundError
from .globals import SUBJECT_ENDPOINT
from .models import Subject, Sample, LibraryDetail
from .requests_helpers import get_request_response_results


def get_subject_from_subject_id(subject_id: str) -> Subject:
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
    try:
        query_results = get_request_response_results(SUBJECT_ENDPOINT, params)
        assert len(query_results) == 1
        return query_results[0]
    except (HTTPError, AssertionError):
        raise SubjectNotFoundError(
            subject_id=subject_id
        )


def get_subject_orcabus_id_from_subject_id(subject_id: str) -> str:
    """
    Get the subject orcabus id from the subject id
    :param subject_id:
    :return:
    """
    return get_subject_from_subject_id(subject_id)['orcabusId']


def get_subject_from_subject_orcabus_id(subject_orcabus_id: str) -> Subject:
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
    try:
        query_results = get_request_response_results(SUBJECT_ENDPOINT, params)
        assert len(query_results) == 1
        return query_results[0]
    except (HTTPError, AssertionError):
        raise SubjectNotFoundError(
            subject_orcabus_id=subject_orcabus_id
        )


def list_samples_in_subject(subject_orcabus_id: str) -> List[Sample]:
    """
    Given a subject id, list the samples in the subject
    :param subject_orcabus_id:
    :return:
    """
    from .. import get_sample_from_sample_orcabus_id

    # Get the subject
    return list(map(
        # For each subject, get libraries in subject
        lambda library_iter_: get_sample_from_sample_orcabus_id(library_iter_['sample']['orcabusId']),
        # Get list of subject orcabus ids
        list_libraries_in_subject(subject_orcabus_id)
    ))


def list_libraries_in_subject(subject_orcabus_id: str) -> List[LibraryDetail]:
    """
    Given a subject id, return the list of library objects in the subject
    :param subject_orcabus_id:
    :return:
    """
    # Get ID For Subject
    subject = get_subject_from_subject_orcabus_id(subject_orcabus_id)
    
    # Get the subject
    return subject.get("librarySet", [])


def get_all_subjects() -> List[Subject]:
    """
    Get all subjects
    :return:
    """
    return get_request_response_results(SUBJECT_ENDPOINT)
