#!/usr/bin/env python3

"""
Helpers for using the contact API endpoint
"""

# Standard imports
from typing import List, Dict
from .globals import WORKFLOW_RUN_ENDPOINT

# Local imports
from .requests_helpers import get_request_response_results, get_request_results_ext, get_request_results


def get_workflow_run(workflow_run_orcabus_id: str) -> Dict:
    """
    Get contact from the contact id
    :param contact_orcabus_id:
    :return:
    """
    # Get contact
    return get_request_results(WORKFLOW_RUN_ENDPOINT, workflow_run_orcabus_id)


def get_workflow_run_from_portal_run_id(portal_run_id: str) -> Dict:
    """
    Get subject from the subject id
    :param contact_id:
    :return:
    """
    # We have an internal id, convert to int
    params = {
        "portalRunId": portal_run_id
    }

    # Get workflow run id
    return get_request_results(
        WORKFLOW_RUN_ENDPOINT,
        get_request_response_results(WORKFLOW_RUN_ENDPOINT, params)[0].get("orcabusId")
    )



def get_workflow_run_state(workflow_run_orcabus_id: str, status: str) -> Dict:
    """
    Get contact from the contact id
    :param contact_orcabus_id:
    :return:
    """
    # Get contact
    return next(
        filter(
            lambda workflow_state_iter_: workflow_state_iter_["status"] == status,
            get_request_results_ext(WORKFLOW_RUN_ENDPOINT, workflow_run_orcabus_id, "state")
        )
    )


