#!/usr/bin/env python3

"""
Get secondary analysis files from library

We also take into consideration the portal run ids list AND the secondaryAnalysisWorkflowList.

We first collect all secondary analysis files associated with this library,
THEN if portalRunId input or secondaryAnalysisWorkflowList is provided, we filter the files based on these lists.
"""

import typing
from typing import Dict, Optional, List
from workflow_tools import get_workflows_from_library_id

if typing.TYPE_CHECKING:
    from metadata_tools import Library

# Initialise the secondary default analysis workflow list
# So that we don't accidentally pick up analyses such as bsshFastqCopy which isn't a real analysis
DEFAULT_SECONDARY_ANALYSIS_WORKFLOW_LIST = [
    "cttsov2", "dragen-tso500-ctdna",
    "tumor-normal", "dragen-wgts-dna",
    "wts", "dragen-wgts-rna"
    "oncoanalyser-wgts-dna",
    "oncoanalyser-wgts-rna",
    "oncoanalyser-wgts-dna-rna",
    "rnasum",
    "umccrise",
    "sash",
]


def handler(event, context) -> Dict[str, List[str]]:
    """
    Get secondary analysis files from library
    :param event:
    :param context:
    :return:
    """

    library: 'Library' = event['library']
    secondary_analysis_workflow_list: Optional[List] = event.get('secondaryAnalysisWorkflowList', None)
    portal_run_id_exclusion_list: Optional[List] = event.get('portalRunIdExclusionList', None)

    library_workflows = get_workflows_from_library_id(library['libraryId'])

    # Filter by workflow type
    if secondary_analysis_workflow_list is None:
        secondary_analysis_workflow_list = DEFAULT_SECONDARY_ANALYSIS_WORKFLOW_LIST
    library_workflows = list(filter(
      lambda workflow_iter_: workflow_iter_['workflowName'].lower() in secondary_analysis_workflow_list,
      library_workflows
    ))

    # Filter by portal run id
    if portal_run_id_exclusion_list is not None:
        library_workflows = list(filter(
          lambda workflow_iter_: workflow_iter_['portalRunId'] not in portal_run_id_exclusion_list,
          library_workflows
        ))

    # Now return the portal run ids from the library workflows
    return {
        "portalRunIds": list(map(
            lambda workflow_iter_: workflow_iter_['portalRunId'],
            library_workflows
        ))
    }
