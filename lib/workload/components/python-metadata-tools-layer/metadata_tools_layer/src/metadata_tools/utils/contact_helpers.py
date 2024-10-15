#!/usr/bin/env python3

"""
Helpers for using the contact API endpoint
"""

# Standard imports
from typing import List, Dict
from .globals import CONTACT_ENDPOINT

# Local imports
from .requests_helpers import get_request_response_results


def get_contact_from_contact_id(contact_id: str) -> Dict:
    """
    Get subject from the subject id
    :param contact_id:
    :return:
    """
    # We have an internal id, convert to int
    params = {
        "contact_id": contact_id
    }

    # Get subject
    return get_request_response_results(CONTACT_ENDPOINT, params)[0]


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
    return get_request_response_results(CONTACT_ENDPOINT, params)[0]


def get_all_contacts() -> List[Dict]:
    """
    Get all subjects
    :return:
    """

    return get_request_response_results(CONTACT_ENDPOINT)
