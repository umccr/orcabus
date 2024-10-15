#!/usr/bin/env python3

from typing import Optional
from pydantic import BaseModel, ConfigDict



class Disease(BaseModel):
    # Attributes
    code: int
    label: Optional[str] = None

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self):
        from ..pieriandx_lookup.get_disease_label import get_disease_label_from_disease_code
        return dict(
            filter(
                lambda dict_object: dict_object[1] is not None,
                {
                    "code": str(self.code),
                    "label":
                        self.label if self.label is not None
                        else get_disease_label_from_disease_code(int(self.code))
                }.items()
            )
        )
