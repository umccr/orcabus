#!/usr/bin/env python3

"""
File Storage Object

The file storage object for the fastq manager is a key pair of ingest_id and s3_uri

However the s3_uri is only available on creation of the object and is not stored in the database
since the s3_uri may change, but the ingest_id is a unique identifier for the file storage object,
we only keep the ingest_id in the database, and if we need the s3 uri we query it from the file manager
"""


# Standard imports
import typing
from os import environ
from typing import Optional, Self, List, Dict
from urllib.parse import urlunparse, urlparse

from dyntastic import Dyntastic
from pydantic import Field, BaseModel, model_validator, ConfigDict
from datetime import datetime

from . import JobStatus, Links, QueryPagination, ResponsePagination

# Util imports
from ..utils import (
    to_snake, to_camel, get_ulid
)
from ..globals import UNARCHIVE_JOB_PREFIX


class JobBase(BaseModel):
    fastq_id_list: List[str]


class JobOrcabusId(BaseModel):
    # fqr.ABCDEFGHIJKLMNOP
    # BCLConvert Metadata attributes
    id: str = Field(default_factory=lambda: f"{UNARCHIVE_JOB_PREFIX}.{get_ulid()}")


class JobWithId(JobBase, JobOrcabusId):
    """
    Order class inheritance this way to ensure that the id field is set first
    """
    # We also have the steps execution id as an attribute to add
    steps_execution_id: Optional[str] = None
    status: JobStatus = Field(default=JobStatus.PENDING)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None


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
        return JobResponse(
            **self.model_dump()
        ).model_dump(by_alias=True)


class JobQueryResponse(BaseModel):
    """
    Job Query Response, includes a list of jobs, the total
    """
    links: Links
    pagination: ResponsePagination
    results: List[JobResponse]

    @classmethod
    def from_results_list(cls, results: List[JobResponse], pagination: QueryPagination, params_response: Dict) -> 'JobQueryResponse':
        # From pagination calculate the links
        url_obj = urlparse(get_unarchiver_api_url())

        params_response = params_response.copy()

        if pagination['page'] == 1:
            previous_page = None
        else:
            params_response['page'] = pagination['page'] - 1
            params_str = "&".join([
                f"{k}={v}"
                for k, v in params_response.items()
            ])

            previous_page = str(urlunparse(
                (url_obj.scheme, url_obj.netloc, url_obj.path, None, params_str, None)
            ))

        if pagination['page'] * pagination['count'] >= pagination['count']:
            next_page = None
        else:
            params_response['page'] = pagination['page'] - 1
            params_str = "&".join([
                f"{k}={v}"
                for k, v in params_response.items()
            ])
            next_page = str(urlunparse(
                (url_obj.scheme, url_obj.netloc, url_obj.path, None, params_str, None)
            ))

        response_pagination = pagination.copy()
        response_pagination['count'] = len(results)

        results_start = ( pagination['page'] - 1 ) * pagination['rowsPerPage']
        results_end = results_start + pagination['rowsPerPage']

        return cls(
            links={
                'previous': previous_page,
                'next': next_page
            },
            pagination=response_pagination,
            results=results[results_start:results_end]
        )

    if typing.TYPE_CHECKING:
        def model_dump(self, **kwargs) -> 'Self':
            pass




