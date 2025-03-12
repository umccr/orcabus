#!/usr/bin/env python3

from enum import Enum
from typing import TypedDict, Optional


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"


class Links(TypedDict):
    previous: Optional[str]
    next: Optional[str]


class QueryPagination(TypedDict):
    page: int
    rowsPerPage: int


class ResponsePagination(QueryPagination):
    count: int


from .job import JobData, JobCreate, JobResponse, JobQueryResponse

__all__ = [
    "JobData",
    "JobCreate",
    "JobResponse",
    "JobQueryResponse"
]


