#!/usr/bin/env python3

# Standard imports
from fastapi.routing import HTTPException
from dyntastic import Dyntastic
from os import environ
from pydantic import Field, BaseModel, model_validator, ConfigDict, AliasGenerator, model_serializer
from typing import Optional, Dict
from enum import Enum
import logging
import json
from decimal import Decimal

# Util imports
from .utils import (
    to_snake_case, get_library_id_from_library_orcabus_id,
    get_presigned_url_from_s3_ingest_id, get_s3_uri_from_s3_ingest_id,
    get_ulid, get_s3_ingest_id_from_s3_uri, get_presigned_url_expiry, str_to_camel_case
)
from .globals import CONTEXT_PREFIX

# Set basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompressionFormat(Enum):
    ORA = 'ORA'
    GZIP = 'GZIP'


class BoolQueryEnum(Enum):
    TRUE = True
    FALSE = False
    ALL = 'ALL'


class Library(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

    orcabus_id: str = Field(default="")
    library_id: str = Field(default="")

    @model_validator(mode='before')
    def confirm_either_orcabus_id_or_library_id(cls, values):
        if 'orcabus_id' not in list(map(to_snake_case, values.keys())) and 'library_id' not in list(map(to_snake_case, values.keys())):
            raise HTTPException(status_code=400, detail="orcabus id or library id is required for library object")
        return values

    @model_validator(mode='before')
    def get_library_id_from_library_orcabus_id(cls, values):
        if 'library_id' not in list(map(to_snake_case, values.keys())):
            values['library_id'] = get_library_id_from_library_orcabus_id(values.get('orcabusId', values.get('orcabus_id')))
        return values

    @model_validator(mode='before')
    def get_library_orcabus_id_from_library_id(cls, values):
        if 'orcabus_id' not in list(map(to_snake_case, values.keys())):
            values['orcabus_id'] = get_library_id_from_library_orcabus_id(values.get('libraryId', values.get('library_id')))
        return values

    def to_dict(self):
        return self.model_dump(by_alias=True)


class FileStorageObject(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

    s3_ingest_id: str = Field(default="")
    s3_uri: Optional[str] = None

    @model_validator(mode='before')
    def set_s3_ingest_id(cls, values):
    # Assign the rgid_ext to the rgid.instrument_run_id
        if 's3_ingest_id' not in list(map(to_snake_case, values.keys())):
            values['s3_ingest_id'] = get_s3_ingest_id_from_s3_uri(values.get("s3Uri", values.get("s3_uri")))
        return values

    def to_dict(self):
        return self.model_dump()

    def model_dump(self, **kwargs):
        return super().model_dump(exclude={"s3_uri"}, by_alias=True, **kwargs)


class FastqPairStorageObject(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

    r1: FileStorageObject
    r2: FileStorageObject

    @model_validator(mode='before')
    def convert_bytes_to_dict(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return values

    def to_dict(self) -> Dict:
        # Complete recursive serialization manually
        data = self.model_dump(by_alias=True)
        data['r1'] = self.r1.to_dict()
        if self.r2:
            data['r2'] = self.r2.to_dict()
        return data


class QcInformation(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

    insert_size_estimate: Decimal = Field(default=Decimal(0))
    raw_wgs_coverage_estimate: Decimal = Field(default=Decimal(0))
    r1_q20_fraction: Decimal = Field(default=Decimal(0))
    r2_q20_fraction: Decimal = Field(default=Decimal(0))
    r1_gc_fraction: Decimal = Field(default=Decimal(0))
    r2_gc_fraction: Decimal = Field(default=Decimal(0))

    @model_validator(mode='before')
    def load_bytes(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return values

    @model_validator(mode='before')
    def convert_floats_to_decimals(cls, values):
        for field, value in values.items():
            if isinstance(value, float):
                values[field] = Decimal(str(value))
        return values

    def to_dict(self) -> Dict:
        return self.model_dump(by_alias=True)


# Custom models for handling patch requests
class ReadCountInfo(BaseModel):
    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

    read_count: int
    base_count_est: int

    @model_validator(mode='before')
    def load_json_string(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return values

    def to_dict(self) -> Dict:
        return self.model_dump(by_alias=True)


class FileCompressionInfo(BaseModel):
    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

    compression_format: CompressionFormat
    gzip_compression_size_in_bytes: int

    @model_validator(mode='before')
    def load_json_string(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return values

    def to_dict(self) -> Dict:
        return self.model_dump(by_alias=True)


class NtsmUri(BaseModel):
    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

    ntsm_uri: str

    @model_validator(mode='before')
    def load_json_string(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return values

    def to_dict(self) -> Dict:
        return self.model_dump(by_alias=True)


class FastqListRow(Dyntastic):
    __table_name__ = environ['DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME']
    # __table_host__ = environ['DYNAMODB_HOST']
    __hash_key__ = "id"

    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: str_to_camel_case(field_name),
            serialization_alias=lambda field_name: str_to_camel_case(field_name),
        )
    )

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
            if 'instrument_run_id' in list(map(to_snake_case, values.keys())):
                values['rgid_ext'] = f"{values['rgid']}.{values.get('instrumentRunId', values.get('instrument_run_id'))}"
            else:
                raise HTTPException(status_code=400, detail="Could not get the instrument run id")
        return values

    # Ensures that the library_orcabus_id is set before the object is saved
    @model_validator(mode='before')
    def set_library_orcabus_id(cls, values):
        # Assign the library_orcabus_id to the library.orcabus_id
        if 'library_orcabus_id' not in values:
            if 'orcabus_id' in list(map(to_snake_case, values['library'].keys())):
                values['library_orcabus_id'] = f"{values['library'].get('orcabusId', values['library'].get('orcabus_id'))}"
            else:
                raise HTTPException(status_code=400, detail="Could not get orcabus id from library")
        return values

    # Response to the client
    def to_dict(self) -> Dict:
        # We don't want to provide rgid_ext or library_orcabus_id to the client
        data = self.model_dump(
            exclude={
                'rgid_ext',
                'library_orcabus_id'
            },
            by_alias=True,
        )

        # Manually set data for object types, qc, library, and files
        # FIXME - I feel like there should be a better way to do this
        # FIXME - rather than manually calling to_dict on each subattribute which is
        # FIXME - also a BaseModel object
        data['qc'] = self.qc.to_dict() if self.qc else None

        # Set the library object
        data['library'] = self.library.to_dict()

        # Set the files object
        data['files'] = self.files.to_dict() if self.files else None

        return data

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
                "location": get_s3_uri_from_s3_ingest_id(self.files.r1.s3_ingest_id)
            },
            "read_2": {
                "class": "File",
                "location": get_s3_uri_from_s3_ingest_id(self.files.r1.s3_ingest_id)
            }
        }

    def presign_uris(self) -> Dict[str, Dict[str, str]]:
        # Get all unarchived files
        # Presign the URIs
        r1_presigned_url = get_presigned_url_from_s3_ingest_id(self.files.r1.s3_ingest_id)
        presigned_objects = {
            "r1": {
                "s3Uri": get_s3_uri_from_s3_ingest_id(self.files.r1.s3_ingest_id),
                "presignedUrl": r1_presigned_url,
                "expiresAt": get_presigned_url_expiry(r1_presigned_url).isoformat(sep="T", timespec="seconds").replace("+00:00", "Z"),
            }
        }
        if self.files.r2:
            r2_presigned_url = get_presigned_url_from_s3_ingest_id(self.files.r2.s3_ingest_id)
            presigned_objects["r2"] = {
                "s3Uri": get_s3_uri_from_s3_ingest_id(self.files.r2.s3_ingest_id),
                "presignedUrl": r2_presigned_url,
                "expiresAt": get_presigned_url_expiry(r2_presigned_url).isoformat(sep="T", timespec="seconds").replace("+00:00", "Z"),
            }

        return presigned_objects




