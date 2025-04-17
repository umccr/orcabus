#!/usr/bin/env python3

"""
Job model, used to for job management
"""

# Standard imports
import typing
from typing import List
from os import environ
from typing import Optional, Self, ClassVar

from dyntastic import Dyntastic
from fastapi.encoders import jsonable_encoder
from pydantic import Field, BaseModel, model_validator, ConfigDict
from datetime import datetime
from enum import Enum

from . import JobStatus, QueryPaginatedResponse

# Util imports
from ..utils import (
    to_camel, get_ulid, get_unarchiver_endpoint_url
)
from ..globals import UNARCHIVE_FASTQ_JOB_PREFIX

class JobType(Enum):
    S3_UNARCHIVING = "S3_UNARCHIVING"


class JobBase(BaseModel):
    fastq_ids: List[str]
    job_type: JobType


class JobOrcabusId(BaseModel):
    # fqr.ABCDEFGHIJKLMNOP
    # BCLConvert Metadata attributes
    id: str = Field(default_factory=lambda: f"{UNARCHIVE_FASTQ_JOB_PREFIX}.{get_ulid()}")


class JobWithId(JobBase, JobOrcabusId):
    """
    Order class inheritance this way to ensure that the id field is set first
    """
    # We also have the steps execution id as an attribute to add
    steps_execution_arn: Optional[str] = None
    status: JobStatus = Field(default=JobStatus.PENDING)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_messages: Optional[str] = None


class JobResponse(JobWithId):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    # Set keys to camel case
    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    # Set the model_dump method response
    if typing.TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class JobCreate(JobBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    def model_dump(self, **kwargs) -> 'JobResponse':
        return (
            JobResponse(**super().model_dump()).
            model_dump()
        )


class JobPatch(BaseModel):
    status: JobStatus


class JobData(JobWithId, Dyntastic):
    """
    The job data object
    """
    __table_name__ = environ['DYNAMODB_UNARCHIVING_JOB_TABLE_NAME']
    __table_host__ = environ['DYNAMODB_HOST']
    __hash_key__ = "id"

    # To Dictionary
    def to_dict(self) -> 'JobResponse':
        """
        Alternative serialization path to return objects by camel case
        :return:
        """
        return jsonable_encoder(
            JobResponse(
                **self.model_dump()
            ).model_dump(by_alias=True)
        )


class JobQueryPaginatedResponse(QueryPaginatedResponse):
    """
    Job Query Response, includes a list of jobs, the total
    """
    url_placeholder: ClassVar[str] = get_unarchiver_endpoint_url()
    results: List[JobResponse]

    @classmethod
    def resolve_url_placeholder(cls, **kwargs) -> str:

        # Get the url placeholder
        return cls.url_placeholder.format()