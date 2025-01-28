#!/usr/bin/env python3

# Standard imports
from typing import Self
import logging
import json
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import Field, BaseModel, model_validator, ConfigDict
from pydantic.alias_generators import to_snake, to_camel

# Set basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QcInformationBase(BaseModel):
    insert_size_estimate: Decimal = Field(default=Decimal(0))
    raw_wgs_coverage_estimate: Decimal = Field(default=Decimal(0))
    r1_q20_fraction: Decimal = Field(default=Decimal(0))
    r2_q20_fraction: Decimal = Field(default=Decimal(0))
    r1_gc_fraction: Decimal = Field(default=Decimal(0))
    r2_gc_fraction: Decimal = Field(default=Decimal(0))


class QcInformationResponse(QcInformationBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    if TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class QcInformationCreate(QcInformationBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def to_camel_case(cls, values):
        return {to_camel(key): value for key, value in values.items()}

    def model_dump(self, **kwargs) -> 'QcInformationResponse':
        return (
            QcInformationResponse(**super().model_dump(**kwargs)).
            model_dump(by_alias=True)
        )


class QcInformationPatch(QcInformationCreate):
    @model_validator(mode='before')
    def load_bytes_and_convert_to_camel(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return {to_camel(k): v for k, v in values.items()}


class QcInformationData(QcInformationBase):
    # Convert keys to snake case prior to validation
    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}

    def to_dict(self) -> 'QcInformationResponse':
        """
        Alternative Serialization method to_dict which uses the Response object
        which allows us to use the camel case keys
        :return:
        """
        return (
            QcInformationResponse(**self.model_dump()).
            model_dump(by_alias=True)
        )
