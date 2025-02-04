#!/usr/bin/env python3

# Standard imports
from dyntastic import Dyntastic
from os import environ
from pydantic import Field, BaseModel, model_validator, ConfigDict, computed_field
from typing import Optional, Self, List, Union

# Layer imports
from filemanager_tools import get_s3_uri_from_ingest_id, get_presigned_url_from_ingest_id, get_presigned_url_expiry, \
    get_s3_uris_from_ingest_ids_map

# Local imports
from . import CWLDict, PresignedUrlModel
from ..cache import update_cache, S3_INGEST_ID_URI_MAP_CACHE
from ..globals import CONTEXT_PREFIX
from ..utils import (
    get_ulid,
    datetime_to_isoformat,
    to_snake, to_camel
)

from .fastq_pair import (
    FastqPairStorageObjectData, FastqPairStorageObjectResponse,
    FastqPairStorageObjectCreate
)
from .file_storage import (
    FileStorageObjectData, FileStorageObjectResponse,
    FileStorageObjectCreate
)

from .library import LibraryData, LibraryResponse
from .qc import QcInformationData, QcInformationResponse, QcInformationCreate


class FastqListRowBase(BaseModel):
    # FastqListRow base attributes
    # Missing the following, id, rgid_ext and library_orcabus_id
    # We add in the 'id' in the FastqListRowResponse model
    # We add in the 'id', 'rgid_ext' and 'library_orcabus_id' in the FastqListRow model
    # However the CreateFastqListRow model does not require these fields to be set
    # So we start with the greatest common denominator and extend classes from there
    rgid: str  # Usually comprises index+index2.lane
    index: str = None
    index2: Optional[str] = None
    lane: int = Field(default=1)
    instrument_run_id: str

    # The library object that this fastq list row is associated with
    library: LibraryData

    # Storage Metadata - This attaches the filemanager information to the fastq list row pairing
    # There may be duplicates since we have a copy in the cache bucket and the archive storage bucket
    read_set: Optional[FastqPairStorageObjectData] = None

    # QC Information
    qc: Optional[QcInformationData] = None

    # Additional metadata
    read_count: Optional[int] = None
    base_count_est: Optional[int] = None

    # Boolean decision-making logic
    is_valid: Optional[bool] = None  # Is the fastq pair valid

    # Future
    ntsm: Optional[FileStorageObjectData] = None


class FastqListRowOrcabusId(BaseModel):
    # fqr.ABCDEFGHIJKLMNOP
    # BCLConvert Metadata attributes
    id: str = Field(default_factory=lambda: f"{CONTEXT_PREFIX}.{get_ulid()}")


class FastqListRowWithId(FastqListRowBase, FastqListRowOrcabusId):
    """
    Order class inheritance this way to ensure that the id field is set first
    """
    pass


class FastqListRowResponse(FastqListRowWithId):
    # Identical to the CreateFastqListRow model but with the addition of the id field
    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    # Manually configure the sub fields with their own model configurations
    library: LibraryResponse

    read_set: Optional[FastqPairStorageObjectResponse] = None

    qc: Optional[QcInformationResponse] = None

    ntsm: Optional[FileStorageObjectResponse] = None

    # Set keys to camel case
    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    # Set the model_dump method response
    def model_dump(self, **kwargs) -> Self:
        # Recursively serialize the object
        data = super().model_dump(**kwargs)

        # Manually serialize the sub fields
        for field_name in ["library", "read_set", "qc", "ntsm"]:
            field = getattr(self, field_name)
            if field is not None:
                data[to_camel(field_name)] = field.model_dump()

        return data


class FastqListRowCreate(FastqListRowBase):
    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    # Manually configure the sub fields with their own model configurations
    library: LibraryResponse

    read_set: Optional[FastqPairStorageObjectCreate] = None

    qc: Optional[QcInformationCreate] = None

    ntsm: Optional[FileStorageObjectCreate] = None

    def model_dump(self, **kwargs) -> 'FastqListRowResponse':
        return (
            FastqListRowResponse(**super().model_dump()).
            model_dump()
        )


class FastqListRowData(FastqListRowWithId, Dyntastic):
    # We don't use aliases, instead we convert all keys to snake case first
    # And then we convert them back to camel case in the to_dict method.
    # This separates out serialization to the database store and serialization to the client
    __table_name__ = environ['DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME']
    __table_host__ = environ['DYNAMODB_HOST']
    __hash_key__ = "id"

    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}

    @computed_field
    def rgid_ext(self) -> str:
        return f"{self.rgid}.{self.instrument_run_id}"

    @computed_field
    def library_orcabus_id(self) -> str:
        return self.library.orcabus_id

    def to_dict(self) -> 'FastqListRowResponse':
        """
        Alternative serialization path to return objects by camel case
        :return:
        """
        return FastqListRowResponse(
            **self.model_dump(
                exclude={"rgid_ext", "library_orcabus_id"}
            )
        ).model_dump(by_alias=True)

    def to_cwl(self) -> CWLDict:
        """
        Return as a CWL input object
        :return:
        """
        return {
            "rgid": self.rgid + f".{self.instrument_run_id}",
            "rglb": self.library.library_id,
            "rgsm": self.library.library_id,
            "lane": self.lane,
            "read_1": {
                "class": "File",
                "location": get_s3_uri_from_ingest_id(self.read_set.r1.s3_ingest_id)
            },
            "read_2": {
                "class": "File",
                "location": get_s3_uri_from_ingest_id(self.read_set.r2.s3_ingest_id)
            }
        }

    def presign_uris(self) -> PresignedUrlModel:
        # Get all unarchived files
        # Presign the URIs
        r1_presigned_url = get_presigned_url_from_ingest_id(self.read_set.r1.s3_ingest_id)
        presigned_objects = {
            "r1": {
                "s3Uri": get_s3_uri_from_ingest_id(self.read_set.r1.s3_ingest_id),
                "presignedUrl": r1_presigned_url,
                "expiresAt": datetime_to_isoformat(get_presigned_url_expiry(r1_presigned_url))
            }
        }
        if self.read_set.r2:
            r2_presigned_url = get_presigned_url_from_ingest_id(self.read_set.r2.s3_ingest_id)
            presigned_objects["r2"] = {
                "s3Uri": get_s3_uri_from_ingest_id(self.read_set.r2.s3_ingest_id),
                "presignedUrl": r2_presigned_url,
                "expiresAt": datetime_to_isoformat(get_presigned_url_expiry(r2_presigned_url))
            }

        return presigned_objects


class FastqListRowListResponse(BaseModel):
    # List response
    fastq_list_rows: List[FastqListRowData]

    def model_dump(self, **kwargs) -> List[FastqListRowResponse]:
        # Collect the s3 ingest ids for the fastq list rows
        fastqs_with_readsets = list(filter(
            lambda fastq_list_row_iter_: fastq_list_row_iter_.read_set is not None,
            self.fastq_list_rows
        ))

        r1_s3_ingest_ids = list(map(
            lambda fastq_list_row_iter_: fastq_list_row_iter_.read_set.r1.s3_ingest_id,
            fastqs_with_readsets
        ))

        # Fixme, read2 may not exist
        r2_s3_ingest_ids = list(map(
            lambda fastq_list_row_iter_: fastq_list_row_iter_.read_set.r2.s3_ingest_id,
            fastqs_with_readsets
        ))

        # Get the
        r1_s3_list_dict = get_s3_uris_from_ingest_ids_map(r1_s3_ingest_ids)

        # Get the r2 s3 uris
        r2_s3_list_dict = get_s3_uris_from_ingest_ids_map(r2_s3_ingest_ids)

        # Update the cache with the s3 uris
        for row in (r1_s3_list_dict + r2_s3_list_dict):
            update_cache(row['ingestId'], row['uri'])

        print(S3_INGEST_ID_URI_MAP_CACHE)
        print("FOO BAR FOO")

        # Now re-dump the fastq list rows
        return list(map(lambda fastq_list_row_iter_: fastq_list_row_iter_.to_dict(), self.fastq_list_rows))


