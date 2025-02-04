#!/usr/bin/env python3

"""
This module contains helper functions for the individual class.
"""

# Standard imports
from typing import List
from requests import HTTPError
from functools import reduce
from operator import concat

# Local imports
from .models import Individual
from .. import list_libraries_in_subject, IndividualNotFoundError
from .globals import INDIVIDUAL_ENDPOINT
from .requests_helpers import get_request_response_results


def get_individual_from_individual_id(individual_id: str) -> Individual:
    """
    Get individual from the individual id
    :param individual_id:
    :return:
    """
    # We have an internal id
    params = {
        "individual_id": individual_id
    }

    # Get individual
    try:
        query_results = get_request_response_results(INDIVIDUAL_ENDPOINT, params)
        assert len(query_results) == 1
        return query_results[0]
    except (HTTPError, AssertionError):
        raise IndividualNotFoundError(
            individual_id=individual_id
        )


def get_individual_orcabus_id_from_individual_id(individual_id: str) -> str:
    return get_individual_from_individual_id(individual_id)["orcabusId"]


def get_individual_from_individual_orcabus_id(individual_orcabus_id: str) -> Individual:
    """
    Get individual from the individual id
    :param individual_orcabus_id:
    :return:
    """
    # We have an internal id
    params = {
        "orcabus_id": individual_orcabus_id
    }

    # Get individual
    try:
        query_results = get_request_response_results(INDIVIDUAL_ENDPOINT, params)
        assert len(query_results) == 1
        return query_results[0]
    except (HTTPError, AssertionError):
        raise IndividualNotFoundError(
            individual_orcabus_id=individual_orcabus_id
        )


def get_all_individuals():
    """
    Get all samples from the sample database
    :return:
    """
    return get_request_response_results(INDIVIDUAL_ENDPOINT)


def list_libraries_in_individual(individual_orcabus_id: str) -> List[Individual]:
    """
    Given an individual id, return all the libraries associated with the individual
    First we need to collect all subjects associated with the individual
    Then we need to collect all libraries associated with the subjects

    :param individual_orcabus_id:
    :return:
    """
    return list(reduce(
        concat,
        list(map(
            # For each subject, get libraries in subject
            lambda subject_iter_: list_libraries_in_subject(subject_iter_['orcabusId']),
            # Get list of subject orcabus ids
            get_individual_from_individual_orcabus_id(individual_orcabus_id)["subjectSet"]
        ))
    ))
