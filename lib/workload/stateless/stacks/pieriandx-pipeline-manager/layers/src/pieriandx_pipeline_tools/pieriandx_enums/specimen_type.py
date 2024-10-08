#!/usr/bin/env python3

from pydantic import BaseModel, ConfigDict
from typing import Optional

from pieriandx_pipeline_tools.pieriandx_lookup.get_specimen_label import get_specimen_label_from_specimen_code


class SpecimenType(BaseModel):
    code: int
    label: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def to_dict(self):
        return dict(
            filter(
                lambda dict_object: dict_object[1] is not None,
                {
                    "code": str(self.code),
                    "label":
                        self.label if self.label is not None
                        else get_specimen_label_from_specimen_code(int(self.code))
                }.items()
            )
        )
