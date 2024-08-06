#!/usr/bin/env python

from typing import Optional
from pydantic import BaseModel


class MedicalFacility(BaseModel):
    facility: Optional[str]
    hospital_number: str

    def to_dict(self):
        return dict(
            filter(
                lambda dict_object: dict_object[1] is not None,
                {
                    "facility": self.facility,
                    "hospitalNumber": self.hospital_number
                }.items()
            )
        )
