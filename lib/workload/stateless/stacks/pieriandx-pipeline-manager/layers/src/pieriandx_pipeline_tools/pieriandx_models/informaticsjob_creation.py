#!/usr/bin/env python3

from pydantic import BaseModel, ConfigDict
from typing import Dict
from .specimen_sequencer_info import SpecimenSequencerInfo


class InformaticsJobCreation(BaseModel):
    # Local imported attributes

    case_accession_number: str
    specimen_sequencer_run_info: SpecimenSequencerInfo

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> Dict:
        # Initialise case dict
        return {
            "input": [
                {
                    "accessionNumber": self.case_accession_number,
                    "sequencerRunInfos": [
                        self.specimen_sequencer_run_info.to_informaticsjob_dict()
                    ]
                }
            ]
        }
