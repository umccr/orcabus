#!/usr/bin/env python

from enum import Enum
from typing import Dict, Optional


class DataType(Enum):
    MICROSAT_OUTPUT = "microsat_output"
    TMB_METRICS = "tmb_metrics"
    CNV = "cnv"
    HARD_FILTERED = "hard_filtered"
    FUSIONS = "fusions"
    METRICS_OUTPUT = "metrics_output"


class DataNameSuffixByDataType(Enum):
    MICROSAT_OUTPUT = ".microsat_output.json"
    TMB_METRICS = ".tmb.metrics.csv"
    CNV = ".cnv.vcf"
    HARD_FILTERED = ".hard-filtered.vcf"
    FUSIONS = "_Fusions.csv"
    METRICS_OUTPUT = "_MetricsOutput.tsv"


PATH_EXTENSION = "Data/Intensities/BaseCalls"


class DataFile:

    def __init__(
        self,
        sequencerrun_path_root,
        file_type: DataType,
        sample_id: str,
        src_uri: Optional[str] = None,
        contents: Optional[str] = None,
    ):
        # Initialise the class variables
        self.sequencerrun_path_root = sequencerrun_path_root
        self.file_type = file_type
        self.sample_id = sample_id
        self.src_uri = src_uri
        self.contents = contents

        # Make sure that the src_uri or contents are provided
        if self.src_uri is None and self.contents is None:
            raise ValueError("Either src_uri or contents must be provided")

        # Determine compression status by src uri file extension
        if self.src_uri.endswith(".gz"):
            self.needs_decompression = True
        else:
            self.needs_decompression = False

        # Determine the destination uri
        self.dest_uri = (
            self.sequencerrun_path_root.rstrip("/") + "/" + PATH_EXTENSION + "/" +
            self.sample_id + DataNameSuffixByDataType[self.file_type.name].value
        )

    def to_dict(self) -> Dict:
        return {
            "src_uri": self.src_uri,
            "dest_uri": self.dest_uri,
            "needs_decompression": self.needs_decompression,
            "contents": self.contents
        }

