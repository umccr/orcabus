#!/usr/bin/env python3

"""
This module contains helper functions for the individual class.
"""

#!/usr/bin/env python3


# !/usr/bin/env python3


"""
Helper functions for a subject
"""

# Standard imports
from typing import Dict

# Local imports
from .globals import INDIVIDUAL_ENDPOINT
from .requests_helpers import get_request_response_results


def get_individual_from_individual_id(individual_id: str) -> Dict:
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
    return get_request_response_results(INDIVIDUAL_ENDPOINT, params)[0]


def get_individual_from_individual_orcabus_id(individual_orcabus_id: str) -> Dict:
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
    return get_request_response_results(INDIVIDUAL_ENDPOINT, params)[0]


def get_all_individuals():
    """
    Get all samples from the sample database
    :return:
    """
    return get_request_response_results(INDIVIDUAL_ENDPOINT)
