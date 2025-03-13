#!/usr/bin/env python3

from typing import Optional, List
from sequence_run_manager_proc.services.v2_samplesheet_parser.models.base_model import SampleSheetSectionBaseModel

class BCLConvertSettingsModel(SampleSheetSectionBaseModel):
    """
    BCLConvert Settings Section
    https://support-docs.illumina.com/SW/dragen_v42/Content/SW/DRAGEN/SampleSheet.htm
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure/bcl-convert-interactive-sample-sheet
    """
    adapter_behavior: Optional[str] = None  # One of 'trim' / 'mask'
    adapter_read_1: Optional[str] = None
    adapter_read_2: Optional[str] = None
    adapter_stringency: Optional[float] = None  # Float between 0.5 and 1.0
    barcode_mismatches_index_1: Optional[int] = None  # 0, 1 or 2
    barcode_mismatches_index_2: Optional[int] = None  # 0, 1 or 2
    minimum_trimmed_read_length: Optional[int] = None
    minimum_adapter_overlap: Optional[int] = None  # 1, 2, or 3
    mask_short_reads: Optional[int] = None
    override_cycles: Optional[str] = None  # Y151;N8;N10;Y151
    trim_umi: Optional[bool] = None  # true or false (1, 0)
    create_fastq_for_index_reads: Optional[bool] = None  # true or false (1, 0)
    no_lane_splitting: Optional[bool] = None
    fastq_compression_format: Optional[str] = None
    find_adapters_with_indels: Optional[bool] = None
    independent_index_collision_check: Optional[List] = None

    # Software version required when running through auto-launch
    # Urn also required when running through auto-launch on BaseSpace
    software_version: Optional[str] = None
    urn: Optional[str] = None


class BCLConvertDataModel(SampleSheetSectionBaseModel):
    """
    BCLConvert Data Row
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure/bcl-convert-interactive-sample-sheet
    """
    sample_id: str
    lane: Optional[int] = None
    index: Optional[str] = None
    index2: Optional[str] = None
    sample_project: Optional[str] = None
    sample_name: Optional[str] = None
    # Per Sample Settings
    override_cycles: Optional[str] = None
    barcode_mismatches_index_1: Optional[int] = None
    barcode_mismatches_index_2: Optional[int] = None
    adapter_read_1: Optional[str] = None
    adapter_read_2: Optional[str] = None
    adapter_behavior: Optional[str] = None
    adapter_stringency: Optional[float] = None

    # Cloud Data
    # If URN is specified in BCLConvert_Settings
    # and no Cloud_Data section is specified we add in the Cloud_Data section for each sample
    # Sample_ID is obvs just sample_id
    # LibraryName is <Sample_ID>_<index>_<index2>
    library_prep_kit_name: Optional[str] = None
    index_adapter_kit_name: Optional[str] = None
