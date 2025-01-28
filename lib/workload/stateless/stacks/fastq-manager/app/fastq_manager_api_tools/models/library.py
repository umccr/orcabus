#!/usr/bin/env python3

"""
Library Object

The library object for the fastq manager is a key pair of library_id and orcabus_id
where library_id can be found in the lab metadata and usually starts with L and is of the syntax
LYY012345

The orcabus_id is the unique identifier for the library in the orcabus database and is of the syntax

We define three separate classes for the library object, since we want to distinguish between
serializing the object for the API response and the serialization of the data store object

The LibraryBase contains the common fields for the library object and is used as the base class for
the other two classes

The LibraryResponse class is used to serialize the library object for the API response and is used
to return the library object in camel case, by using the alias_generator and setting 'by_alias' to True
when invoking the model_dump method, the object is returned in camel case

However alias_generator sets both the validation alias AND the serialization alias, so to ensure
that both inputs of {"library_id": "LYY012345"} and {"libraryId": "LYY012345"} are accepted, we
need to use the model_validator to convert the keys to camel case before validation
"""

# Standard imports
from typing import Self
from typing import TYPE_CHECKING

from fastapi.routing import HTTPException
from pydantic import Field, BaseModel, model_validator, ConfigDict
from pydantic.alias_generators import to_camel, to_snake


# Util imports
from ..utils import (
    get_library_id_from_library_orcabus_id,
)

class LibraryBase(BaseModel):
    orcabus_id: str = Field(default="")
    library_id: str = Field(default="")


class LibraryResponse(LibraryBase):
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    if TYPE_CHECKING:
        def model_dump(self, **kwargs) -> Self:
            pass


class LibraryData(LibraryBase):
    @model_validator(mode='before')
    def convert_keys_to_snake_case(cls, values):
        return {to_snake(k): v for k, v in values.items()}

    @model_validator(mode='after')
    def confirm_either_orcabus_id_or_library_id(self) -> Self:
        if self.orcabus_id == "" and self.library_id == "":
            raise HTTPException(status_code=400, detail="orcabus id or library id is required for library object")
        elif self.library_id == "":
            self.library_id = get_library_id_from_library_orcabus_id(self.orcabus_id)
        elif self.orcabus_id == "":
            self.orcabus_id = get_library_id_from_library_orcabus_id(self.library_id)
        return self

    def to_dict(self) -> 'LibraryResponse':
        """
        Alternative serialization path to return objects by camel case
        :return:
        """
        return LibraryResponse(**self.model_dump()).model_dump(by_alias=True)
