#!/usr/bin/env python3

"""
SFN LAMBDA FUNCTION PLACEHOLDER: __get_workflow_run_id_from_portal_run_id_lambda_function_arn__

Get workflow for portal run id

"""

from typing import Dict

from workflow_tools import (
    WorkflowRun,
    get_workflow_run_from_portal_run_id,
)


def handler(event, context) -> Dict[str, WorkflowRun]:
    """
    Get the portal run id, and return as a workflow object
    :param event:
    :param context:
    :return:
    """
    portal_run_id = event['portalRunId']
    workflow = get_workflow_run_from_portal_run_id(portal_run_id)

    return {
        'workflowRunObject': workflow
    }