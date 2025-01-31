#!/usr/bin/env python3

# Standard imports
import json
from typing import Self
from typing import TYPE_CHECKING

from pydantic import BaseModel, model_validator, ConfigDict
from pydantic.alias_generators import to_snake, to_camel


# Custom models for handling patch requests
class ReadCountInfoBase(BaseModel):
    # Set the model configuration
    read_count: int
    base_count_est: int


class ReadCountInfoResponse(ReadCountInfoBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    if TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class ReadCountInfoCreate(ReadCountInfoBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    def model_dump(self, **kwargs) -> 'ReadCountInfoResponse':
        return (
            ReadCountInfoResponse(**super().model_dump(**kwargs)).
            model_dump(**kwargs)
        )


class ReadCountInfoPatch(BaseModel):
    read_count_obj: ReadCountInfoCreate

    def model_dump(self, **kwargs) -> 'ReadCountInfoResponse':
        return (
            ReadCountInfoResponse(**dict(self.read_count_obj.model_dump(**kwargs))).
            model_dump(**kwargs)
        )


class ReadCountInfoData(ReadCountInfoBase):
    # Convert keys to snake case prior to validation
    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}

    def to_dict(self) -> 'ReadCountInfoResponse':
        """
        Alternative Serialization method to_dict which uses the Response object
        which allows us to use the camel case keys
        :return:
        """
        return (
            ReadCountInfoResponse(**self.model_dump()).
            model_dump(by_alias=True)
        )
