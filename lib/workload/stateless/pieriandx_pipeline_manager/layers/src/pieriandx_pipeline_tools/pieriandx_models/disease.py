#!/usr/bin/env python3

from typing import Optional
from pydantic import BaseModel, ConfigDict


class Disease(BaseModel):
    # Attributes
    code: str
    label: Optional[str] = None

    # Model configuration
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
