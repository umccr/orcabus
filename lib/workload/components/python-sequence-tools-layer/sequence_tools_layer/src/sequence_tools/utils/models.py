#!/usr/bin/env python3

from typing import TypedDict, Literal, NotRequired, Optional, Dict

statusLiteral = Literal['STARTED', 'FAILED', 'SUCCEEDED', 'ABORTED', 'RESOLVED']


class SequenceDetail(TypedDict):
    orcabusId: str
    instrumentRunId: str
    experimentName: str
    startTime: str
    endTime: str
    status: statusLiteral


class Sequence(TypedDict):
    orcabusId: str
    libraries: str
    sequenceRunId: str
    status: statusLiteral
    startTime: str
    sampleSheetName: str
    v1pre3Id: str
    icaProjectId: str
    apiUrl: str
    endTime: str
    runVolumeName: str
    runFolderPath: str
    runDataUri: str
    instrumentRunId: str
    reagentBarcode: str
    flowcellBarcode: str
    sequenceRunName: str
    experimentName: str


class SampleSheet(TypedDict):
    orcabusId: str
    sampleSheetName: str
    associationStatus: str
    associationTimestamp: str
    sampleSheetContent: Optional[Dict]
    sequence: str