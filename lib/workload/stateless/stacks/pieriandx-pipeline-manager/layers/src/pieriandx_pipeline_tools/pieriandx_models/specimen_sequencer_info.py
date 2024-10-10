#!/usr/bin/env python3

from pydantic import BaseModel, ConfigDict
from typing import Dict

class SpecimenSequencerInfo(BaseModel):
    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    case_accession_number: str
    barcode: str
    lane: int
    sample_id: str
    sample_type: str

    def to_dict(self) -> Dict:
        return {
            "accessionNumber": self.case_accession_number,
            "barcode": self.barcode,
            "lane": str(self.lane),
            "sampleId": self.sample_id,
            "sampleType": self.sample_type
        }

    def to_informaticsjob_dict(self) -> Dict:
        return {
            "runId": self.run_id,
            "barcode": self.barcode,
            "lane": str(self.lane),
            "sampleId": self.sample_id,
            "sampleType": self.sample_type
        }
