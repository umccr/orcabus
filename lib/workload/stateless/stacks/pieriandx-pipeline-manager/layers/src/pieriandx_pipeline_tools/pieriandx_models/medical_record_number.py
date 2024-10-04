#!/usr/bin/env python
from pydantic import BaseModel
from .medical_facility import MedicalFacility


class MedicalRecordNumber(BaseModel):
    mrn: str
    medical_facility: MedicalFacility

    def to_dict(self):
        return {
            "mrn": self.mrn,
            "medicalFacility": self.medical_facility.to_dict()
        }
