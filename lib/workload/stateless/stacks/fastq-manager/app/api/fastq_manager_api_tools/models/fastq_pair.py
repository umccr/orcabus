# Standard imports
from typing import Optional, TypedDict, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, model_validator, ConfigDict

# Local imports
from . import CompressionFormatEnum
from ..utils import (
    to_snake, to_camel
)

# Model imports
from .file_storage import (
    FileStorageObjectData, FileStorageObjectResponse,
    FileStorageObjectCreate, FileStorageObjectBase, FileStorageObjectResponseWithNoS3DetailsDict,
    FileStorageObjectResponseWithS3DetailsDict,

)

# Create class for a single fastq storage object
class FastqStorageObjectBase(FileStorageObjectBase):
    gzip_compression_size_in_bytes: Optional[int] = None
    raw_md5sum: Optional[str] = None


class FastqStorageObjectResponseDictWithS3DetailsDict(FileStorageObjectResponseWithS3DetailsDict):
    gzipCompressionSizeInBytes: Optional[int]
    rawMd5sum: Optional[str]


class FastqStorageObjectResponseDictWithNoS3DetailsDict(FileStorageObjectResponseWithNoS3DetailsDict):
    gzipCompressionSizeInBytes: Optional[int]
    rawMd5sum: Optional[str]


FastqStorageObjectResponseDict = Union[FastqStorageObjectResponseDictWithS3DetailsDict, FastqStorageObjectResponseDictWithNoS3DetailsDict]


class FastqStorageObjectResponse(FastqStorageObjectBase, FileStorageObjectResponse):
    def model_dump(self, **kwargs) -> FastqStorageObjectResponseDict:
        include_s3_details = False
        if 'include_s3_details' in kwargs:
            kwargs = kwargs.copy()
            include_s3_details = kwargs.pop('include_s3_details')

        # Get model dumps from each parent class separately
        # Only grab the gzip_compression_size_in_bytes and raw_md5sum from the FastqStorageObjectBase
        fastq_data = dict(filter(
            lambda kv: to_snake(kv[0]) in ['gzip_compression_size_in_bytes', 'raw_md5sum'],
            FastqStorageObjectBase.model_dump(self, **kwargs).items()
        ))
        file_data = FileStorageObjectResponse.model_dump(
            self,
            **kwargs, include_s3_details=include_s3_details
        )

        return jsonable_encoder(
            dict(
                **fastq_data,
                **file_data
            )
        )

class FastqStorageObjectCreate(FastqStorageObjectBase, FileStorageObjectCreate):
    pass

class FastqStorageObjectData(FastqStorageObjectBase, FileStorageObjectData):
    pass


# Base class
class FastqPairStorageObjectBase(BaseModel):
    r1: FastqStorageObjectData
    r2: Optional[FastqStorageObjectData] = None

    # Compression format information
    compression_format: Optional[CompressionFormatEnum] = None


# Response classes
class FastqPairStorageObjectResponseDict(TypedDict):
    r1: FastqStorageObjectResponseDict
    r2: Optional[FastqStorageObjectResponseDict]
    compressionFormat: Optional[CompressionFormatEnum]


class FastqPairStorageObjectResponse(FastqPairStorageObjectBase):
    r1: FastqStorageObjectResponse
    r2: Optional[FastqStorageObjectResponse] = None

    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    def model_dump(self, **kwargs) -> FastqPairStorageObjectResponseDict:
        # Handle specific kwargs
        include_s3_details = False
        if 'include_s3_details' in kwargs:
            kwargs = kwargs.copy()
            include_s3_details = kwargs.pop('include_s3_details')

        # Complete recursive serialization manually
        data = super().model_dump(**kwargs)

        if 'by_alias' not in kwargs:
            kwargs['by_alias'] = True

        # Serialize r1 and r2
        data['r1'] = self.r1.model_dump(**kwargs, include_s3_details=include_s3_details)
        if self.r2:
            data['r2'] = self.r2.model_dump(**kwargs, include_s3_details=include_s3_details)
        return data


class FastqPairStorageObjectCreate(FastqPairStorageObjectBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )
    r1: FastqStorageObjectCreate
    r2: Optional[FastqStorageObjectCreate] = None


    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    def model_dump(self, **kwargs) -> 'FastqPairStorageObjectResponseDict':
        return (
            FastqPairStorageObjectResponse(**super().model_dump(**kwargs)).
            model_dump(**kwargs)
        )


class FastqPairStorageObjectPatch(BaseModel):
    fastq_pair_storage_obj: FastqPairStorageObjectCreate

    def model_dump(self, **kwargs) -> 'FastqPairStorageObjectResponseDict':
        return (
            FastqPairStorageObjectResponse(
                **dict(self.fastq_pair_storage_obj.model_dump(**kwargs))
            ).
            model_dump(**kwargs)
        )


class FastqPairStorageObjectData(FastqPairStorageObjectBase):
    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}

    def to_dict(self) -> 'FastqPairStorageObjectResponseDict':
        return FastqPairStorageObjectResponse(**self.model_dump()).model_dump()

