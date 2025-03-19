#!/usr/bin/env python

"""
Get workflows from library id
"""

# Standard imports
from typing import List


# Local imports
from .requests_helpers import get_request_response_results
from .globals import WORKFLOW_RUN_ENDPOINT
from .models import WorkflowRunDetail


def get_workflows_from_library_id(library_id: str) -> List[WorkflowRunDetail]:
    """
    Use the query libraries__libraryId to get workflows from a library id
    :param library_id:
    :return:
    """
    return get_request_response_results(
        WORKFLOW_RUN_ENDPOINT,
        params={
            "libraries__libraryId": library_id
        }
    )
