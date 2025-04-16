#!/usr/bin/env python3

"""
Job model, used to for job management
"""
# Standard imports
import typing
from typing import List, TypedDict, Self
from os import environ
from typing import Optional, ClassVar

from dyntastic import Dyntastic
from fastapi.encoders import jsonable_encoder
from pydantic import Field, BaseModel, ConfigDict, model_validator, computed_field
from datetime import datetime, timedelta
from enum import Enum

from data_sharing_tools.utils.models import SecondaryAnalysisDataTypeEnum
from . import JobStatus, QueryPaginatedResponse

# Util imports
from ..utils import (
    to_camel, get_ulid, get_packaging_endpoint_url, get_s3_packaging_prefix, to_snake
)
from ..globals import PACKAGE_CONTEXT_PREFIX

class JobType(Enum):
    S3_UNARCHIVING = "S3_UNARCHIVING"


class DataType(Enum):
    FASTQ = "FASTQ"
    SECONDARY_ANALYSIS = "SECONDARY_ANALYSIS"


class PackageRequestBase(BaseModel):
    library_id_list: Optional[List[str]] = None
    subject_id_list: Optional[List[str]] = None
    individual_id_list: Optional[List[str]] = None
    project_id_list: Optional[List[str]] = None
    instrument_run_id_list: Optional[List[str]] = None
    portal_run_id_list: Optional[List[str]] = None
    portal_run_id_exclusion_list: Optional[List[str]] = None
    data_type_list: Optional[List[DataType]] = None
    secondary_analysis_type_list: Optional[List[SecondaryAnalysisDataTypeEnum]] = None
    defrost_archived_fastqs: Optional[bool] = None

    @model_validator(mode="after")
    def validate_single_metadata_object(self) -> Self:
        if (
                len(
                    list(filter(
                        lambda attr_iter_: attr_iter_ is not None,
                        [self.library_id_list, self.subject_id_list, self.individual_id_list, self.project_id_list]
                    ))
                ) > 1
        ):
            raise ValueError("Expected only one of library_id_list, subject_id_list, individual_id_list, or project_id_list to be set.")
        return self


class PackageRequestCreate(PackageRequestBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    # Set keys to camel case
    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    def model_dump(self, **kwargs) -> 'PackageRequestResponseDict':
        # Wrap model dump in jsonable_encoder
        # Handles the conversion of enums to strings
        return jsonable_encoder(
            PackageRequestResponse(**dict(super().model_dump(**kwargs))).model_dump(
                **kwargs
            )
        )


class PackageRequestResponseDict:
    libraryIdList: Optional[List[str]]
    subjectIdList: Optional[List[str]]
    individualIdList: Optional[List[str]]
    projectIdList: Optional[List[str]]
    instrumentRunIdList: Optional[List[str]]
    portalRunIdList: Optional[List[str]]
    portalRunIdExclusionList: Optional[List[str]]
    dataTypeList: Optional[List[DataType]]
    secondaryAnalysisTypeList: Optional[List[SecondaryAnalysisDataTypeEnum]]
    defrostArchivedFastqs: Optional[bool]


class PackageRequestResponse(PackageRequestBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    def model_dump(self, **kwargs) -> PackageRequestResponseDict:
        if 'by_alias' not in kwargs:
            kwargs = kwargs.copy()
            kwargs['by_alias'] = True
        if 'exclude_none' not in kwargs:
            kwargs = kwargs.copy()
            kwargs['exclude_none'] = True
        return super().model_dump(**kwargs)


class PackageBase(BaseModel):
    """
    Base class for the package
    """
    # Package name must not contain any spaces or special characters
    package_name: str = Field(pattern=r"^[A-Za-z][\w+-_]+$")
    package_request: PackageRequestBase


class PackageOrcabusId(BaseModel):
    # fqr.ABCDEFGHIJKLMNOP
    # BCLConvert Metadata attributes
    id: str = Field(default_factory=lambda: f"{PACKAGE_CONTEXT_PREFIX}.{get_ulid()}")


class PackageWithId(PackageBase, PackageOrcabusId):
    """
    Order class inheritance this way to ensure that the id field is set first
    """
    # We also have the steps execution id as an attribute to add
    package_s3_sharing_prefix: str = Field(default_factory=lambda data: get_s3_packaging_prefix(data['id']))
    steps_execution_arn: Optional[str] = None
    status: JobStatus = Field(default=JobStatus.PENDING)
    request_time: datetime = Field(default_factory=datetime.now)
    completion_time: Optional[datetime] = None


class PackageResponseDict(TypedDict):
    id: str
    packageName: str
    stepsExecutionArn: str
    status: JobStatus
    requestTime: datetime
    completionTime: Optional[datetime]
    hasExpired: bool


class PackageResponse(PackageWithId):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    package_request: PackageRequestResponse

    @computed_field
    def has_expired(self) -> bool:
        return (
            True if PackageData(**self.model_dump()).is_expired()
            else False
        )

    # Set the model_dump method response
    def model_dump(self, **kwargs) -> PackageResponseDict:
        kwargs = kwargs.copy()

        # Check if exclude is set
        # If not, we exclude the package_request body, it may be
        # too large to return on the API, but we store it in our database.
        # Users can list specific items in the package request using specific endpoints.
        if "exclude" not in kwargs:
            kwargs["exclude"] = {"package_request", "package_s3_sharing_prefix"}

        # Check if by_alias is set
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True

        return jsonable_encoder(super().model_dump(**kwargs))


class PackageCreate(PackageBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    package_request: PackageRequestCreate

    # Set keys to camel case
    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    if typing.TYPE_CHECKING:
        def model_dump(self, **kwargs) -> 'Self':
            pass


class PackageData(PackageWithId, Dyntastic):
    """
    The job data object
    """
    __table_name__ = environ['DYNAMODB_PACKAGING_JOB_TABLE_NAME']
    __table_host__ = environ['DYNAMODB_HOST']
    __hash_key__ = "id"

    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}

    # To Dictionary
    def to_dict(self) -> 'PackageResponseDict':
        """
        Alternative serialization path to return objects by camel case
        :return:
        """
        return jsonable_encoder(
            PackageResponse(
                **self.model_dump()
            ).model_dump(by_alias=True)
        )

    def model_dump(self, **kwargs):
        # Wrap model dump in jsonable_encoder
        # Handles the conversion of enums to strings
        return jsonable_encoder(
            super().model_dump(**kwargs)
        )

    def is_expired(self):
        return (
            True if (self.request_time + timedelta(days=30)) < datetime.now()
            else False
        )


class PackageQueryPaginatedResponse(QueryPaginatedResponse):
    """
    Job Query Response, includes a list of jobs, the total
    """
    url_placeholder: ClassVar[str] = get_packaging_endpoint_url()
    results: List[PackageResponseDict]

    @classmethod
    def resolve_url_placeholder(cls, **kwargs) -> str:

        # Get the url placeholder
        return cls.url_placeholder.format()