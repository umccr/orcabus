# Standard imports
from typing import Self, Optional
from pydantic import BaseModel, model_validator, ConfigDict

# Local imports
from . import CompressionFormat
from ..utils import (
    to_snake, to_camel
)

# Model imports
from .file_storage import (
    FileStorageObjectData, FileStorageObjectResponse,
    FileStorageObjectCreate, FileStorageObjectBase
)

# Create class for a single fastq storage object
class FastqStorageObjectBase(FileStorageObjectBase):
    gzip_compression_size_in_bytes: Optional[int] = None
    raw_md5sum: Optional[str] = None


# Define the response, create and data classes
class FastqStorageObjectResponse(FastqStorageObjectBase, FileStorageObjectResponse):
    pass


class FastqStorageObjectCreate(FastqStorageObjectBase, FileStorageObjectCreate):
    pass


class FastqStorageObjectData(FastqStorageObjectBase, FileStorageObjectData):
    pass


# Base class
class FastqPairStorageObjectBase(BaseModel):
    r1: FastqStorageObjectData
    r2: Optional[FastqStorageObjectData] = None

    # Compression format information
    compression_format: Optional[CompressionFormat] = None


# Response class
class FastqPairStorageObjectResponse(FastqPairStorageObjectBase):
    r1: FastqStorageObjectResponse
    r2: Optional[FastqStorageObjectResponse] = None

    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    def model_dump(self, **kwargs) -> Self:
        # Complete recursive serialization manually
        data = super().model_dump(**kwargs)

        # Serialize r1 and r2
        data['r1'] = self.r1.model_dump(by_alias=True)
        if self.r2:
            data['r2'] = self.r2.model_dump(by_alias=True)
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

    def model_dump(self, **kwargs) -> 'FastqPairStorageObjectResponse':
        return (
            FastqPairStorageObjectResponse(**super().model_dump(**kwargs)).
            model_dump(**kwargs)
        )


class FastqPairStorageObjectPatch(BaseModel):
    fastq_pair_storage_obj: FastqPairStorageObjectCreate

    def model_dump(self, **kwargs) -> 'FastqPairStorageObjectResponse':
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

    def to_dict(self) -> 'FastqPairStorageObjectResponse':
        return FastqPairStorageObjectResponse(**self.model_dump()).model_dump()