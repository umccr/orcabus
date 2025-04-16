#!/usr/bin/env python3

"""

Pretty much identical to fq unarchiving object

Push jobs are separate to the packaging processes.
"""
from pathlib import Path
from urllib.parse import urlunparse

#!/usr/bin/env python3

"""
Job model, used to for job management
"""

# Standard imports
import typing
from typing import List
from os import environ
from typing import Optional, Self, ClassVar, TypedDict

from dyntastic import Dyntastic
from fastapi.encoders import jsonable_encoder
from pydantic import Field, BaseModel, model_validator, ConfigDict
from datetime import datetime
from . import JobStatus, QueryPaginatedResponse

# Util imports
from ..utils import (
    to_camel, get_ulid, get_push_endpoint_url, get_push_logs_uri
)
from ..globals import PUSH_JOB_CONTEXT_PREFIX


class PushJobBase(BaseModel):
    step_functions_execution_arn: str
    status: JobStatus
    start_time: datetime
    package_id: str
    share_destination: str


class PushJobOrcabusId(BaseModel):
    # fqr.ABCDEFGHIJKLMNOP
    # BCLConvert Metadata attributes
    id: str = Field(default_factory=lambda: f"{PUSH_JOB_CONTEXT_PREFIX}.{get_ulid()}")


class PushJobWithId(PushJobBase, PushJobOrcabusId):
    """
    Order class inheritance this way to ensure that the id field is set first
    """
    # We also have the steps execution id as an attribute to add
    log_uri: str = Field(default_factory=lambda data: get_push_logs_uri(data['id']))
    end_time: Optional[datetime] = None
    error_messages: Optional[str] = None


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


class PushJobResponse(PushJobWithId):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    # Set keys to camel case
    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    # Set the model_dump method response
    if typing.TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class PushJobCreate(PushJobBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    def model_dump(self, **kwargs) -> 'PushJobResponse':
        return (
            PushJobResponse(**super().model_dump()).
            model_dump()
        )


class PushJobPatch(BaseModel):
    status: JobStatus


class PushLocationBody(BaseModel):
    shareDestination: str


class PushJobData(PushJobWithId, Dyntastic):
    """
    The job data object
    """
    __table_name__ = environ['DYNAMODB_PUSH_JOB_TABLE_NAME']
    __table_host__ = environ['DYNAMODB_HOST']
    __hash_key__ = "id"

    # To Dictionary
    def to_dict(self) -> 'PushJobResponse':
        """
        Alternative serialization path to return objects by camel case
        :return:
        """
        return jsonable_encoder(
            PushJobResponse(
                **self.model_dump()
            ).model_dump(by_alias=True)
        )


class PushJobQueryPaginatedResponse(QueryPaginatedResponse):
    """
    Job Query Response, includes a list of jobs, the total
    """
    url_placeholder: ClassVar[str] = get_push_endpoint_url()
    results: List[PushJobResponse]

    @classmethod
    def resolve_url_placeholder(cls, **kwargs) -> str:

        # Get the url placeholder
        return cls.url_placeholder.format()