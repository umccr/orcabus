#!/usr/bin/env python3

from typing import Optional
from sequence_run_manager_proc.services.v2_samplesheet_parser.models.base_model import SampleSheetSectionBaseModel

class TSO500LSettingsModel(SampleSheetSectionBaseModel):
    """
    TSO500L Settings Section
    https://support-docs.illumina.com/SW/DRAGEN_TSO500_ctDNA_v2.1/Content/SW/Informatics/APP/InputReqs_appT500ctDNAlocal.htm
    https://support.illumina.com/content/dam/illumina-support/documents/documentation/software_documentation/trusight/trusight-oncology-500/200034937-00-dragen-trusight-oncology-ctdna-500-analysis-software-v211-ica-user-guide.pdf
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure/section-requirements
    """
    # BCLConvert Settings for within TSO500L
    adapter_read_1: Optional[str] = None
    adapter_read_2: Optional[str] = None
    adapter_behaviour: Optional[str] = None
    minimum_trimmed_read_length: Optional[int] = None
    mask_short_reads: Optional[int] = None
    override_cycles: Optional[str] = None

    # Settings
    starts_from_fastq: Optional[bool] = None

    # Cloud values
    software_version: Optional[str] = None
    urn: Optional[str] = None

class TSO500LDataModel(SampleSheetSectionBaseModel):
    """
    TSO500L Data Row
    https://support-docs.illumina.com/SW/DRAGEN_TSO500_ctDNA_v2.1/Content/SW/Informatics/APP/InputReqs_appT500ctDNAlocal.htm
    https://support.illumina.com/content/dam/illumina-support/documents/documentation/software_documentation/trusight/trusight-oncology-500/200034937-00-dragen-trusight-oncology-ctdna-500-analysis-software-v211-ica-user-guide.pdf
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure/section-requirements
    """
    sample_id: str
    index_id: Optional[str] = None  # Use when using [Cloud_TSO500L_Data]
    sample_type: str
    sample_description: Optional[str] = None
    lane: Optional[int] = None
    index: str
    index2: str
    i7_index_id: Optional[str] = None  # Use when using [TSO500L_Data]
    i5_index_id: Optional[str] = None  # Use when using [TSO500L_Data]

    # Cloud Data
    # If URN is specified in TSO500L_Settings
    # and no Cloud_Data section is specified we add in the Cloud_Data section for each sample
    # Sample_ID is obvs just sample_id
    # LibraryName is <Sample_ID>_<index>_<index2>
    library_prep_kit_name: Optional[str] = None
    index_adapter_kit_name: Optional[str] = None
