#!/usr/bin/env python3

"""
Helpers for using the contact API endpoint
"""

# Standard imports
from typing import List, Dict

from requests import HTTPError

from .globals import CONTACT_ENDPOINT, ORCABUS_ULID_REGEX_MATCH
from .models import Contact

# Local imports
from .requests_helpers import get_request_response_results
from .. import ContactNotFoundError


def get_contact_from_contact_id(contact_id: str) -> Contact:
    """
    Get contact from the contact id
    :param contact_id:
    :return:
    """
    # We have an internal id, convert to int
    params = {
        "contact_id": contact_id
    }

    # Get contact
    try:
        query_list = get_request_response_results(CONTACT_ENDPOINT, params)
        assert len(query_list) == 1
        return query_list[0]
    except (HTTPError, AssertionError):
        raise ContactNotFoundError(
            contact_id=contact_id,
        )


def get_contact_orcabus_id_from_contact_id(contact_id: str) -> str:
    return get_contact_from_contact_id(contact_id)['orcabusId']


def get_contact_from_contact_orcabus_id(contact_orcabus_id: str) -> Dict:
    """
    Get contact from the contact id
    :param contact_orcabus_id:
    :return:
    """
    params = {
        "orcabus_id": contact_orcabus_id.split(".")[1]
    }

    # Get contact
    try:
        query_result = get_request_response_results(CONTACT_ENDPOINT, params)
        assert len(query_result) == 1
        return query_result[0]
    except (HTTPError, AssertionError):
        raise ContactNotFoundError(
            contact_orcabus_id=contact_orcabus_id,
        )


def coerce_contact_id_or_orcabus_id_to_contact_orcabus_id(id_: str) -> str:
    if ORCABUS_ULID_REGEX_MATCH.match(id_):
        return id_
    else :
        return get_contact_orcabus_id_from_contact_id(id_)


def get_all_contacts() -> List[Contact]:
    """
    Get all subjects
    :return:
    """
    return get_request_response_results(CONTACT_ENDPOINT)
