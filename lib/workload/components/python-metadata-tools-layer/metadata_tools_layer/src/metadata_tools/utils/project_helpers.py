#!/usr/bin/env python3

"""
Helpers for using the project API endpoint
"""

# Standard imports
from typing import List, Dict
from .globals import PROJECT_ENDPOINT

# Local imports
from .requests_helpers import get_request_response_results


def get_project_from_project_id(project_id: str) -> Dict:
    """
    Get subject from the subject id
    :param project_id:
    :return:
    """
    # We have an internal id, convert to int
    params = {
        "project_id": project_id
    }

    # Get subject
    return get_request_response_results(PROJECT_ENDPOINT, params)[0]


def get_project_from_project_orcabus_id(project_orcabus_id: str) -> Dict:
    """
    Get project from the project id
    :param project_orcabus_id:
    :return:
    """
    params = {
        "orcabus_id": project_orcabus_id.split(".")[1]
    }

    # Get project
    return get_request_response_results(PROJECT_ENDPOINT, params)[0]


def get_all_projects() -> List[Dict]:
    """
    Get all subjects
    :return:
    """

    return get_request_response_results(PROJECT_ENDPOINT)
