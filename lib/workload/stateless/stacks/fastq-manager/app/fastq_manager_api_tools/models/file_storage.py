#!/usr/bin/env python3

"""
File Storage Object

The file storage object for the fastq manager is a key pair of s3_ingest_id and s3_uri

However the s3_uri is only available on creation of the object and is not stored in the database
since the s3_uri may change, but the s3_ingest_id is a unique identifier for the file storage object,
we only keep the s3_ingest_id in the database, and if we need the s3 uri we query it from the file manager
"""


# Standard imports
from typing import Optional, Self
from typing import TYPE_CHECKING
import json

from pydantic import Field, BaseModel, model_validator, ConfigDict
from pydantic.alias_generators import to_snake, to_camel

# Util imports
from ..utils import (
    get_s3_ingest_id_from_s3_uri
)


class FileStorageObjectBase(BaseModel):
    s_3_ingest_id: str = Field(default="")


class FileStorageObjectResponse(FileStorageObjectBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    if TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class FileStorageObjectCreate(FileStorageObjectBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    # The s3 uri of the file storage object is only available on creation
    s_3_uri: Optional[str] = None

    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    @model_validator(mode='after')
    def set_s3_ingest_id(self) -> Self:
        # Set the s3 ingest id if not provided to be from the s3 uri
        if not self.s_3_ingest_id:
            self.s_3_ingest_id = get_s3_ingest_id_from_s3_uri(self.s_3_uri)
        return self

    def model_dump(self, **kwargs) -> 'FileStorageObjectResponse':
        return (
            FileStorageObjectResponse(**super().model_dump(exclude={"s3_uri"}, **kwargs)).
            model_dump(by_alias=True)
        )


class FileStorageObjectUpdate(FileStorageObjectCreate):
    @model_validator(mode='before')
    def load_bytes_and_convert_to_camel(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return {to_camel(k): v for k, v in values.items()}


class FileStorageObjectData(FileStorageObjectBase):
    # Convert keys to snake case prior to validation
    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}


    def to_dict(self) -> 'FileStorageObjectResponse':
        """
        Alternative Serialization method to_dict which uses the Response object
        which allows us to use the camel case keys
        :return:
        """
        return (
            FileStorageObjectResponse(**self.model_dump()).
            model_dump(by_alias=True)
        )
