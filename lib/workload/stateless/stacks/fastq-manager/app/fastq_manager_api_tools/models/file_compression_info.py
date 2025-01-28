#!/usr/bin/env python3

# Standard imports
import json
from typing import Self
from typing import TYPE_CHECKING
from pydantic import BaseModel, model_validator, ConfigDict
from pydantic.alias_generators import to_snake, to_camel

# Local
from . import CompressionFormat


class FileCompressionInfoBase(BaseModel):
    compression_format: CompressionFormat
    gzip_compression_size_in_bytes: int


class FileCompressionInfoResponse(FileCompressionInfoBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    if TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class FileCompressionInfoCreate(FileCompressionInfoBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    def model_dump(self, **kwargs) -> 'FileCompressionInfoResponse':
        return (
            FileCompressionInfoResponse(**super().model_dump(**kwargs)).
            model_dump(by_alias=True)
        )


class FileCompressionInfoPatch(FileCompressionInfoCreate):
    @model_validator(mode='before')
    def load_bytes_and_convert_to_camel(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return {to_camel(k): v for k, v in values.items()}


class FileCompressionInfoData(FileCompressionInfoBase):
    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}


    def to_dict(self) -> 'FileCompressionInfoResponse':
        """
        Alternative Serialization method to_dict which uses the Response object
        which allows us to use the camel case keys
        :return:
        """
        return (
            FileCompressionInfoResponse(**self.model_dump()).
            model_dump(by_alias=True)
        )


