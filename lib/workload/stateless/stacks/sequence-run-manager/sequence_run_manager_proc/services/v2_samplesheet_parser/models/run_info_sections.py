#!/usr/bin/env python3

from typing import Optional, List
from sequence_run_manager_proc.services.v2_samplesheet_parser.models.base_model import SampleSheetSectionBaseModel


class HeaderModel(SampleSheetSectionBaseModel):
    """
    The header section contains much of the experiment management configurations
    https://support-docs.illumina.com/SHARE/SampleSheetv2/Content/SHARE/SampleSheetv2/SectionsRunSetup.htm(deprecated)
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure
    """
    file_format_version: Optional[int] = None
    run_name: Optional[str] = None
    run_description: Optional[str] = None
    instrument_platform: Optional[str] = None
    instrument_type: Optional[str] = None
    index_orientation: Optional[str] = None

class ReadsModel(SampleSheetSectionBaseModel):
    """
    The reads section contains the cycle information
    https://support-docs.illumina.com/SHARE/SampleSheetv2/Content/SHARE/SampleSheetv2/SectionsRunSetup.htm(deprecated)
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure
    """
    read_1_cycles: int
    read_2_cycles: Optional[int] = None
    index_1_cycles: Optional[int] = None
    index_2_cycles: Optional[int] = None


class SequencingModel(SampleSheetSectionBaseModel):
    """
    The reads section contains the cycle information
    https://support-docs.illumina.com/SHARE/SampleSheetv2/Content/SHARE/SampleSheetv2/Parameters.htm(deprecated)
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure
    """
    custom_index_1_primer: Optional[bool] = None
    custom_index_2_primer: Optional[bool] = None
    custom_read_1_primer: Optional[bool] = None
    custom_read_2_primer: Optional[bool] = None
    library_prep_kits: Optional[List[str]] = None