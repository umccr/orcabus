#!/usr/bin/env python3

# Standard imports
from typing import Self
import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import Field, BaseModel, model_validator, ConfigDict

from . import FloatDecimal

from ..utils import to_camel, to_snake

# Set basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QcInformationBase(BaseModel):
    insert_size_estimate: FloatDecimal = Field(default=Decimal(0))
    raw_wgs_coverage_estimate: FloatDecimal = Field(default=Decimal(0))
    r1_q20_fraction: FloatDecimal = Field(default=Decimal(0))
    r2_q20_fraction: FloatDecimal = Field(default=Decimal(0))
    r1_gc_fraction: FloatDecimal = Field(default=Decimal(0))
    r2_gc_fraction: FloatDecimal = Field(default=Decimal(0))


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


class QcInformationPatch(BaseModel):
    qc_obj: QcInformationCreate

    def model_dump(self, **kwargs) -> 'QcInformationResponse':
        return (
            QcInformationResponse(**dict(self.qc_obj.model_dump(**kwargs))).
            model_dump(**kwargs)
        )


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
