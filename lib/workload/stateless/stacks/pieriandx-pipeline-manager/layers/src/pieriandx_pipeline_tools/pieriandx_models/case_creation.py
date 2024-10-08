#!/usr/bin/env python3

from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict
# Local imported attributes
from .dag import Dag
from .disease import Disease

from pieriandx_pipeline_tools.pieriandx_enums.sample_type import SampleType
from .specimen import Specimen
from .physician import Physician
from .specimen import IdentifiedSpecimen, DeIdentifiedSpecimen


class CaseCreation(BaseModel):
    dag: Dag
    disease: Disease
    is_identified: bool
    indication: Optional[str] = None
    panel_name: str
    sample_type: SampleType
    specimen: Specimen

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> Dict:
        # Initialise case dict
        case_dict = {
            "identified": self.is_identified,
            "indication": self.indication,
            "panelName": self.panel_name,
            "sampleType": self.sample_type.value,
            "specimens": [self.specimen.to_dict()],
        }

        # Update dag
        case_dict.update(
            self.dag.to_dict()
        )

        # Update disease
        case_dict.update(
            {
                "disease": self.disease.to_dict()
            }
        )

        return case_dict


class IdentifiedCaseCreation(CaseCreation):
    requesting_physician: Physician
    specimen: IdentifiedSpecimen
    is_identified: bool = True

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> Dict:
        # Get the dictionary from the parent class
        initial_dict = super().to_dict()

        # Update the dictionary with the physician and specimen
        initial_dict.update(
            {
                "physicians": [self.requesting_physician.to_dict()],
            }
        )

        return initial_dict


class DeIdentifiedCaseCreation(CaseCreation):
    specimen: DeIdentifiedSpecimen
    is_identified: bool = False

    # Model configuration
    model_config = ConfigDict(from_attributes=True)
