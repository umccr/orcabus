#!/usr/bin/env python3

from pydantic import BaseModel, ConfigDict
from .specimen_sequencer_info import SpecimenSequencerInfo
from pieriandx_pipeline_tools.pieriandx_enums.sequencing_type import SequencingType


class SequencerrunCreation(BaseModel):

    # Sequencer run information
    run_id: str
    specimen_sequence_info: SpecimenSequencerInfo
    sequencing_type: SequencingType

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self):
        return {
            "runId": self.run_id,
            "specimens": [self.specimen_sequence_info.to_dict()],
            "type": self.sequencing_type.value
        }
