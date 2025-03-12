#!/usr/bin/env python3

"""
TypedDict models

Workflow Run is (when the workflow is queried directly
{
  "orcabusId": "wfr.01JDTT7CEYQ0K2E6MCRB9GKX3T",
  "currentState": {
    "orcabusId": "stt.01JE15KJ57R24SEPZZ710MDMDM",
    "status": "SUCCEEDED",
    "timestamp": "2024-12-01T13:12:22.071000Z"
  },
  "libraries": [
    {
      "orcabusId": "lib.01JBMTM4SYY7QH03HM6XF6X0TT",
      "libraryId": "L2000696"
    },
    ...
  ],
  "workflow": {
    "orcabusId": "wfl.01JD7C2HWVR5KF7VWWQPH0M0FZ",
    "workflowName": "ora-compression",
    "workflowVersion": "4-2-4--v2",
    "executionEngine": "Unknown",
    "executionEnginePipelineId": "Unknown"
  },
  "analysisRun": null,
  "portalRunId": "20241122b2e1f778",
  "executionId": null,
  "workflowRunName": "umccr--automated--ora-compression--4-2-4--v2--20241122b2e1f778",
  "comment": null
}

When the workflow is queried from the workflow run list


State is

Payload is
"""

# Imports
from typing import TypedDict, Optional, Dict, List


# Classes
class StateDetail(TypedDict):
    orcabusId: str
    status: str
    timestamp: str


class Workflow(TypedDict):
    orcabusId: str
    workflowName: str
    workflowVersion: str


class State(StateDetail):
    comment: str
    workflowRun: str
    payload: str


class WorkflowRunDetail(TypedDict):
    orcabusId: str
    currentState: StateDetail
    workflow: Workflow
    portalRunId: str
    executionId: Optional[str]
    workflowRunName: str
    comment: Optional[str]
    analysisRun: Optional[str]


class WorkflowRun(WorkflowRunDetail):
    libraries: List[Dict[str, str]]


class Payload(TypedDict):
    orcabusId: str
    payloadRefId: str
    version: str
    data: Dict