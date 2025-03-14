#!/usr/bin/env python3

"""
SFN LAMBDA FUNCTION PLACEHOLDER: __list_files_with_portal_run_id_attribute_lambda_function_arn__

Given a portal run id, this script will return a list of all files associated with that run id.

# FIXME - raise error if the file class is not available storage

# FIXME - also need to filter out files that should not be shared
# FIXME - but this will take some time to sort. For now, just return all files
"""

import typing
from typing import List, Dict

from filemanager_tools import (
    FileObject,
    list_files_from_portal_run_id
)

if typing.TYPE_CHECKING:
    from workflow_tools import WorkflowRun


def handler(event, context) -> Dict[str, List['FileObject']]:
    """
    Given a portal run id, this script will return a list of all files associated with that run id.
    :param event:
    :param context:
    :return:
    """

    # Get the portal run id from the event
    workflow_object: 'WorkflowRun' = event['workflowObject']

    # Get the portal run id from the workflow object
    portal_run_id = workflow_object['portalRunId']

    # Get the list of files associated with the portal run id
    file_obj_list = list_files_from_portal_run_id(portal_run_id)

    return {
        "s3ObjectIdList": list(map(lambda file_object_iter_: file_object_iter_['s3ObjectId'], file_obj_list))
    }
