#!/usr/bin/env python3
from typing import Optional, Dict

from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
# Local imported attributes
from pieriandx_pipeline_tools.pieriandx_enums.ethnicity import Ethnicity
from pieriandx_pipeline_tools.pieriandx_enums.race import Race
from pieriandx_pipeline_tools.pieriandx_enums.gender import Gender
from pieriandx_pipeline_tools.pieriandx_enums.specimen_type import SpecimenType
from .medical_record_number import MedicalRecordNumber


class Specimen(BaseModel):
    case_accession_number: str
    date_accessioned: datetime
    date_received: datetime
    date_collected: datetime
    ethnicity: Optional[Ethnicity] = None
    external_specimen_id: str
    specimen_label: str
    race: Optional[Race] = None
    gender: Optional[Gender] = None
    hl_7_specimen_id: Optional[str] = None
    specimen_type: SpecimenType

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> Dict:
        return dict(
            filter(
                lambda dict_object: dict_object[1] is not None,
                {
                    "accessionNumber": self.case_accession_number,
                    "dateAccessioned": self.date_accessioned.astimezone(timezone.utc).isoformat(sep="T", timespec="seconds").replace("+00:00", "Z"),
                    "dateReceived": self.date_received.astimezone(timezone.utc).isoformat(sep="T", timespec="seconds").replace("+00:00", "Z"),
                    "datecollected": self.date_collected.astimezone(timezone.utc).isoformat(sep="T", timespec="seconds").replace("+00:00", "Z"),
                    "ethnicity": self.ethnicity.value if self.ethnicity is not None else None,
                    "externalSpecimenId": self.external_specimen_id,
                    "gender": self.gender.value if self.gender is not None else None,
                    "hl7SpecimenId": self.hl_7_specimen_id,
                    "name": self.specimen_label,
                    "race": self.race.value if self.race is not None else None,
                    "type": self.specimen_type.to_dict()
                }.items()
            )
        )


class IdentifiedSpecimen(Specimen):

    # Required for Identified specimens
    first_name: str
    last_name: str
    date_of_birth: datetime
    medical_record_number: MedicalRecordNumber

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self):
        return dict(
            filter(
                lambda dict_object: dict_object[1] is not None,
                {
                    **super().to_dict(),
                    "firstName": self.first_name,
                    "lastName": self.last_name,
                    "dateOfBirth": self.date_of_birth.strftime("%Y-%m-%d"),
                    "medicalRecordNumbers": [self.medical_record_number.to_dict()]
                }.items()
            )
        )


class DeIdentifiedSpecimen(Specimen):
    # Required for De-Identified specimens
    study_identifier: str
    study_subject_identifier: str
