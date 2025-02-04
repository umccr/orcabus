#!/usr/bin/env python3

"""
Helpers for using the project API endpoint
"""

# Standard imports
from typing import List, Dict

from requests import HTTPError

from .errors import ProjectNotFoundError
from .globals import PROJECT_ENDPOINT, LIBRARY_ENDPOINT
from .models import Project, Library

# Local imports
from .requests_helpers import get_request_response_results


def get_project_from_project_id(project_id: str) -> Project:
    """
    Get project from the project id
    :param project_id:
    :return:
    """
    # We have an internal id, convert to int
    params = {
        "project_id": project_id
    }

    # Get project
    try:
        query_results = get_request_response_results(PROJECT_ENDPOINT, params)
        assert len(query_results) == 1
        return query_results[0]
    except (HTTPError, AssertionError) as e:
        raise ProjectNotFoundError(
            project_id=project_id,
        )


def get_project_orcabus_id_from_project_id(project_id: str) -> str:
    return get_project_from_project_id(project_id)["orcabusId"]


def get_project_from_project_orcabus_id(project_orcabus_id: str) -> Project:
    """
    Get project from the project id
    :param project_orcabus_id:
    :return:
    """
    params = {
        "orcabus_id": project_orcabus_id.split(".")[1]
    }

    # Get project
    try:
        query_results = get_request_response_results(PROJECT_ENDPOINT, params)
        assert len(query_results) == 1
        return query_results[0]
    except (HTTPError, AssertionError) as e:
        raise ProjectNotFoundError(
            project_id=project_orcabus_id,
        )


def get_all_projects() -> List[Project]:
    """
    Get all projects
    :return:
    """
    return get_request_response_results(PROJECT_ENDPOINT)


def list_libraries_in_project(project_orcabus_id: str) -> List[Library]:
    """
    List all libraries in a project
    Use the projectSet__orcabusId query

    :return:
    """
    params = {
        "projectSet__orcabusId": project_orcabus_id
    }

    return get_request_response_results(LIBRARY_ENDPOINT, params)
