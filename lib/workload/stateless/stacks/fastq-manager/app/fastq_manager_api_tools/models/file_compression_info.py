#!/usr/bin/env python3

# Standard imports
from typing import Self, Optional
from typing import TYPE_CHECKING
from pydantic import BaseModel, model_validator, ConfigDict

# Local
from . import CompressionFormat
from ..utils import to_camel, to_snake


class FileCompressionInfoBase(BaseModel):
    compression_format: CompressionFormat
    r1_gzip_compression_size_in_bytes: int
    r2_gzip_compression_size_in_bytes: Optional[int] = None


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
            model_dump(**kwargs)
        )


class FileCompressionInfoPatch(BaseModel):
    file_compression_obj: FileCompressionInfoCreate

    def model_dump(self, **kwargs) -> 'FileCompressionInfoResponse':
        return (
            FileCompressionInfoResponse(**dict(self.file_compression_obj.model_dump(**kwargs))).
            model_dump(**kwargs)
        )


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


