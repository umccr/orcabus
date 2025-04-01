#!/usr/bin/env python3

"""
{
  "id": "ufr.01JJY7P1AVFGHGVMEDE8T4VWJG",
  "jobType: "S3_UNARCHIVING",
  "stepsExecutionArn": "aws:arn:states:us-east-1:123456789012:execution:myStateMachine:myExecution",
  "status": "SUCCEEDED",
  "startTime": "2021-07-01T00:00:00Z",
  "endTime": "2021-07-01T00:00:00Z",
}
"""

from typing import (
    TypedDict,
)

from enum import Enum


class JobType(Enum):
    S3_UNARCHIVING = "S3_UNARCHIVING"


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    SUCCEEDED = "SUCCEEDED"


class Job(TypedDict):
    id: str
    jobType: JobType
    stepsExecutionArn: str
    status: JobStatus
    startTime: str
    endTime: str
    errorMessages: str