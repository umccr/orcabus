#!/usr/bin/env python3

"""
This file contains the models for the database.
"""

import typing
from typing import Union, TypedDict, NotRequired, List, Dict
from pathlib import Path
from enum import Enum
from datetime import datetime
from typing import Optional
from filemanager_tools import FileObject


class DataTypeEnum(Enum):
    FASTQ = "fastq"
    SECONDARY_ANALYSIS = "secondaryAnalysis"


class FileObjectWithRelativePathTypeDef(FileObject):
    dataType: DataTypeEnum
    relativePath: Union[Path, str]


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    SUCCEEDED = "SUCCEEDED"


class FileObjectWithPresignedUrlTypeDef(FileObjectWithRelativePathTypeDef):
    presignedUrl: str
    relativePath: Union[Path, str]


class SecondaryAnalysisDataTypeEnum(Enum):
    # CURRENT
    TUMOR_NORMAL = "tumor-normal"
    WTS = "wts"
    CTTSOV2 = "cttsov2"

    # FUTURE
    DRAGEN_WGTS_DNA = 'dragen-wgts-dna'
    DRAGEN_WGTS_RNA = 'dragen-wgts-rna'
    DRAGEN_TSO500_CTDNA = 'dragen-tso500-ctdna'

    # ONCOANALYSER
    ONCOANALYSER_WGTS_DNA = 'oncoanalyser-wgts-dna'
    ONCOANALYSER_WGTS_RNA = 'oncoanalyser-wgts-rna'
    ONCOANALYSER_WGTS_DNA_RNA = 'oncoanalyser-wgts-dna-rna'

    SASH = 'sash'
    UMCCRISE = 'umccrise'
    RNASUM = 'rnasum'


class PackageResponseDict(TypedDict):
    id: str
    packageName: str
    stepsExecutionArn: str
    status: JobStatus
    requestTime: datetime
    completionTime: datetime


class PushJobResponseDict(TypedDict):
    id: str
    stepFunctionsExecutionArn: str
    status: JobStatus
    startTime: datetime
    packageId: str
    shareDestination: str
    logUri: str
    endTime: Optional[datetime]
    errorMessage: Optional[str]


class WorkflowRunModelSlim(TypedDict):
    orcabusId: str
    timestamp: str
    portalRunId: str
    workflowName: str
    workflowVersion: str
    libraries: NotRequired[List[Dict[str, str]]]

