#!/usr/bin/env python3
from fastapi.routing import HTTPException


from dyntastic import Dyntastic
from os import environ
from pydantic import Field, BaseModel, model_validator

from .utils import (
    to_snake_case, get_library_id_from_library_orcabus_id,
    get_presigned_url_from_s3_ingest_id, get_s3_uri_from_s3_ingest_id,
    get_ulid, to_camel_case, get_s3_ingest_id_from_s3_uri
)

from typing import Optional, Dict
from enum import Enum

CONTEXT_PREFIX = "fqr"


class CompressionFormat(Enum):
    ORA = 'ORA'
    GZIP = 'GZIP'


class BoolQueryEnum(Enum):
    TRUE = True
    FALSE = False
    ALL = 'ALL'


class Library(BaseModel):
    orcabus_id: Field(default="")
    library_id: Field(default="")

    @model_validator(mode='before')
    def confirm_either_orcabus_id_or_library_id(cls, values):
        if 'orcabus_id' not in list(map(to_snake_case, values.keys())) and 'library_id' not in list(map(to_snake_case, values.keys())):
            raise HTTPException(status_code=400, detail="orcabus id or library id is required for library object")
        return values

    @model_validator(mode='before')
    def get_library_id_from_library_orcabus_id(cls, values):
        if 'library_id' not in list(map(to_snake_case, values.keys())):
            values['library_id'] = get_library_id_from_library_orcabus_id(values['orcabusId'])
        return values

    @model_validator(mode='before')
    def get_library_orcabus_id_from_library_id(cls, values):
        if 'orcabus_id' not in list(map(to_snake_case, values.keys())):
            values['orcabus_id'] = get_library_id_from_library_orcabus_id(values['libraryId'])
        return values


class FileStorageObject(BaseModel):
    s3_ingest_id: Field(default="")
    s3_uri: Optional[str]

    @model_validator(mode='before')
    def set_s3_ingest_id(cls, values):
    # Assign the rgid_ext to the rgid.instrument_run_id
        if 's3_ingest_id' not in values:
            values['s3_ingest_id'] = get_s3_ingest_id_from_s3_uri(values['s3_uri'])
        return values

    def to_dict(self):
        self.model_dump(
            exclude={"s3_uri"}
        )


class FastqPairStorageObject(BaseModel):
    r1: FileStorageObject
    r2: FileStorageObject


class QcInformation(BaseModel):
    insert_size_estimate: float
    raw_wgs_coverage_estimate: float
    r1_q20_fraction: float
    r2_q20_fraction: float
    r1_gc_fraction: float
    r2_gc_fraction: float


class FastqListRow(Dyntastic):
    __table_name__ = environ['DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME']
    __table_host__ = environ['DYNAMODB_HOST']
    __hash_key__ = "id"

    # This key is hidden from the client
    # But used in the database
    rgid_ext: str = Field(default="")  # Usually comprises index+index2.lane.instrument_run_id
    # This key is hidden from the client
    # But is used as an index in the database
    library_orcabus_id: str = Field(default="")

    # fqr.ABCDEFGHIJKLMNOP
    # BCLConvert Metadata attributes
    id: str = Field(default_factory=lambda: f"{CONTEXT_PREFIX}.{get_ulid()}")
    rgid: str  # Usually comprises index+index2.lane
    index: Optional[str] = None
    index2: Optional[str] = None
    lane: Optional[int] = None
    instrument_run_id: str

    # The library object that this fastq list row is associated with
    library: Library

    # Storage Metadata - This attaches the filemanager information to the fastq list row pairing
    # There may be duplicates since we have a copy in the cache bucket and the archive storage bucket
    files: Optional[FastqPairStorageObject] = None

    # QC Information
    qc: Optional[QcInformation] = None

    # Additional metadata
    read_count: Optional[int] = None
    base_count_est: Optional[int] = None

    # Boolean decision-making logic
    is_valid: Optional[bool] = None  # Is the fastq pair valid

    # Compression format information
    compression_format: Optional[CompressionFormat] = None
    gzip_compression_size_in_bytes: Optional[int] = None

    # Future
    ntsm_uri: Optional[str] = None

    # Ensures that the rgid_ext is set before the object is saved
    @model_validator(mode='before')
    def set_rgid_ext(cls, values):
        # Assign the rgid_ext to the rgid.instrument_run_id
        if 'rgid_ext' not in values:
            values['rgid_ext'] = f"{values['rgid']}.{values['instrumentRunId']}"
        return values

    # Ensures that the library_orcabus_id is set before the object is saved
    @model_validator(mode='before')
    def set_library_orcabus_id(cls, values):
        # Assign the library_orcabus_id to the library.orcabus_id
        if 'library_orcabus_id' not in values:
            values['library_orcabus_id'] = f"{values['library']['orcabusId']}"
        return values

    # Response to the client
    def to_dict(self) -> Dict:
        # We don't want to provide rgid_ext or library_orcabus_id to the client
        return to_camel_case(
            self.model_dump(
                exclude={'rgid_ext', 'library_orcabus_id'}
            )
        )

    def to_cwl(self) -> Dict:
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
                "location": self.files.read1_file_object.s3_ingest_id
            },
            "read_2": {
                "class": "File",
                "location": self.files.read2_file_object.s3_ingest_id
            }
        }

    def presign_uris(self) -> Dict[str, Dict[str, str]]:
        # Get all unarchived files
        # Presign the URIs
        r1_presigned_url = get_presigned_url_from_s3_ingest_id(self.files.r1.s3_ingest_id)
        presigned_objects = {
            "read1": {
                "s3Uri": get_s3_uri_from_s3_ingest_id(self.files.r1.s3_ingest_id),
                "presignedUrl": r1_presigned_url['presignedUrl'],
                "expiresAt": r1_presigned_url['expiresAt'],
            }
        }
        if self.files.r2:
            r2_presigned_url = get_presigned_url_from_s3_ingest_id(self.files.r2.s3_ingest_id)
            presigned_objects["read2"] = {
                "s3Uri": get_s3_uri_from_s3_ingest_id(self.files.r2.s3_ingest_id),
                "presignedUrl": r2_presigned_url['presignedUrl'],
                "expiresAt": r2_presigned_url['expiresAt'],
            }

        return presigned_objects
