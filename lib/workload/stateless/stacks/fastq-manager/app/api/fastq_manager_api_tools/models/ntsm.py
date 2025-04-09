#!/usr/bin/env python3

# Standard imports
from pydantic import BaseModel, model_validator
from typing import Self
import logging
import json
from typing import TYPE_CHECKING
from .file_storage import FileStorageObjectResponse, FileStorageObjectData, FileStorageObjectCreate


# Set basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NtsmUriBase(BaseModel):
    ntsm: FileStorageObjectData


class NtsmUriResponse(NtsmUriBase):
    ntsm: FileStorageObjectResponse

    if TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class NtsmUriCreate(NtsmUriBase):
    ntsm: FileStorageObjectCreate

    def model_dump(self, **kwargs) -> 'NtsmUriResponse':
        return (
            NtsmUriResponse(**super().model_dump()).
            model_dump()
        )


class NtsmUriUpdate(NtsmUriCreate):
    @model_validator(mode='before')
    def load_json_string(cls, values):
        if isinstance(values, bytes):
            values = json.loads(values.decode('utf-8'))
        return values


class NtsmUriData(NtsmUriBase):
    def to_dict(self) -> 'NtsmUriResponse':
        # Complete recursive serialization manually
        data = self.model_dump()
        data['ntsm'] = self.ntsm.to_dict()
        return NtsmUriResponse(**data).model_dump(by_alias=True)
