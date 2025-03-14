#!/usr/bin/env python3

"""
Helpers for using the contact API endpoint
"""

# Standard imports
from typing import Dict
from requests import HTTPError

# Local imports
from .globals import WORKFLOW_RUN_ENDPOINT
from .requests_helpers import get_request_response_results, get_request_results_ext, get_request_results
from .models import WorkflowRun, State


def get_workflow_run(workflow_run_orcabus_id: str) -> WorkflowRun:
    """
    Get the workflow run from the workflow run id
    :param workflow_run_orcabus_id:
    :return:
    """
    # Get workflow run
    try:
        return get_request_results(WORKFLOW_RUN_ENDPOINT, workflow_run_orcabus_id)
    except HTTPError as e:
        from .errors import WorkflowRunNotFoundError
        raise WorkflowRunNotFoundError(workflow_run_id=workflow_run_orcabus_id) from e


def get_workflow_run_from_portal_run_id(portal_run_id: str) -> WorkflowRun:
    """
    Get workflow run from the portal run id
    :param portal_run_id:
    :return:
    """
    # We have an internal id, convert to int
    params = {
        "portalRunId": portal_run_id
    }

    try:
        return get_request_results(
            WORKFLOW_RUN_ENDPOINT,
            get_request_response_results(WORKFLOW_RUN_ENDPOINT, params)[0].get("orcabusId")
        )
    except HTTPError as e:
        from .errors import WorkflowRunNotFoundError
        raise WorkflowRunNotFoundError(portal_run_id=portal_run_id) from e


def get_workflow_run_state(workflow_run_orcabus_id: str, status: str) -> State:
    """
    Get workflow run state from the workflow run orcabus id
    :param workflow_run_orcabus_id:
    :param status:
    :return:
    """
    # Get workflow run state
    try:
        return next(
            filter(
                lambda workflow_state_iter_: workflow_state_iter_["status"] == status,
                get_request_results_ext(WORKFLOW_RUN_ENDPOINT, workflow_run_orcabus_id, "state")
            )
        )
    except HTTPError as e:
        from .errors import WorkflowRunStateNotFoundError
        raise WorkflowRunStateNotFoundError(
            workflow_run_id=workflow_run_orcabus_id,
            status=status
        ) from e

