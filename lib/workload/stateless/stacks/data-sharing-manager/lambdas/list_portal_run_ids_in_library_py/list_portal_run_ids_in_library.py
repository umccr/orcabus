#!/usr/bin/env python3

"""

SFN LAMBDA PLACEHOLDER: __list_portal_run_ids_in_library_lambda_function_arn__

List portal run ids from the library.

We also retrieve the portal run id exclusion list, so we filter out any portal run ids
that are in the exclusion list.
"""

import typing
from typing import List, Dict

from workflow_tools import (
    WorkflowRunDetail,
    get_workflows_from_library_id
)

if typing.TYPE_CHECKING:
    from metadata_tools import Library


def handler(event, context) -> Dict[str, List[str]]:
    """
    Given a library object, list the portal run ids in the library
    :param event:
    :param context:
    :return:
    """

    # Get library object
    library: 'Library' = event['libraryObject']
    portal_run_id_exclusion_list: List[str] = event['portalRunIdExclusionList']
    secondary_analyses_type_list: List[str] = event['secondaryAnalysisTypeList']

    # List portal run ids in the library
    workflows_list: List[WorkflowRunDetail] = get_workflows_from_library_id(library['libraryId'])

    # Filter workflows not in the secondary analyses list
    workflows_list = list(filter(
        lambda workflow_iter_: workflow_iter_['workflow']['workflowName'] in secondary_analyses_type_list,
        workflows_list
    ))

    portal_run_ids_list = list(map(
        lambda workflow_iter_: workflow_iter_['portalRunId'],
        workflows_list
    ))

    # Filter workflows in the exclusion list
    if portal_run_id_exclusion_list:
        portal_run_ids_list = list(filter(
            lambda portal_run_id_iter_: portal_run_id_iter_ not in portal_run_id_exclusion_list,
            portal_run_ids_list
        ))


    return {
        'portalRunIdList': portal_run_ids_list
    }
