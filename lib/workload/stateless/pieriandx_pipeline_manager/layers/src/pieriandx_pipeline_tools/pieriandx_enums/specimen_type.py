#!/usr/bin/env python3

from pydantic import BaseModel, ConfigDict
from typing import Optional


class SpecimenType(BaseModel):
    code: str
    label: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def to_dict(self):
        return dict(
            filter(
                lambda dict_object: dict_object[1] is not None,
                {
                    "code": self.code,
                    "label": self.label
                }.items()
            )
        )
