#!/usr/bin/env python

"""
GLOBALS used in projects

* METADATA SPREAD SHEET
* SAMPLE SHEET REGEXES
* GOOGLE LIMS
* LOGS

"""

import re
from typing import List

from v2_samplesheet_maker.enums import FastqCompressionFormat

METADATA_COLUMN_NAMES = {
  "library_id": 'LibraryID',  # the internal ID for the library
  "sample_name": 'SampleName',  # the sample name assigned by the lab
  "sample_id": 'SampleID',  # the internal ID for the sample
  "external_sample_id": 'ExternalSampleID',  # the external ID for the sample
  "subject_id": 'SubjectID',  # the internal ID for the subject/patient
  "external_subject_id": "ExternalSubjectID",  # The external subject ID
  "phenotype": 'Phenotype',  # tumor, normal, negative-control, ...
  "quality": 'Quality',  # Good, Poor, Borderline
  "source": 'Source',  # tissue, FFPE, ...
  "project_name": 'ProjectName',
  "project_owner": 'ProjectOwner',
  "experiment_id": "ExperimentID",
  "type": 'Type',  # the sample type: WGS, WTS, 10X, ...
  "assay": "Assay",  # the assay type; TsqNano, NebRNA ...
  "override_cycles": "OverrideCycles",  # The Override cycles list for this run
  "secondary_analysis": "Workflow",  # ?
  "coverage": "Coverage (X)",  # ?
  "truseq_index": "TruSeq Index, unless stated",  # FIXME - this is a terrible column name
  "run": "Run#",
  "comments": "Comments",
  "rrna": "rRNA",
  "qpc_id": "qPCR ID",
  "sample_id_samplesheet": "Sample_ID (SampleSheet)"  # FIXME - this is named 'Sample_ID (SampleSheet)' in the dev spreadsheet
}


"""
METADATA SPREAD SHEET 
"""

METADATA_VALIDATION_COLUMN_NAMES = {
       "val_phenotype": "PhenotypeValues",
       "val_quality": "QualityValues",
       "val_source": "SourceValues",
       "val_type": "TypeValues",
       "val_project_name": "ProjectNameValues",
       "val_project_owner": "ProjectOwnerValues",
}

#METADATA_COLUMN_NAMES.update(METADATA_VALIDATION_COLUMN_NAMES)

"""
SAMPLE SHEET DATA COLUMNS
"""

REQUIRED_SAMPLE_SHEET_DATA_COLUMN_NAMES = {
    "v1": ["Sample_ID", "Sample_Name", "index"],
    "v2": ["Sample_ID", "index"]
}

VALID_SAMPLE_SHEET_DATA_COLUMN_NAMES = {
    # This is the standard
    "v1": ["Lane", "Sample_ID", "Sample_Name", "Sample_Plate", "Sample_Well",
           "Index_Plate_Well", "I7_Index_ID", "index",
           "I5_Index_ID", "index2", "Sample_Project", "Description"],
    # This is the future
    "v2": ["Lane", "Sample_ID", "index", "index2", "Sample_Project"]
}


"""
SAMPLE SHEET REGEXES
"""

EXPERIMENT_REGEX_STR = {
    "top_up": r"(?:_topup\d?)",
    "rerun": r"(?:_rerun\d?)"
}

SAMPLE_ID_REGEX_STR = {
    "sample_id_non_control": r"(?:PRJ|CCR|MDX|TGX)\d{6}",
    "sample_id_control": r"(?:NTC|PTC)_\w+"
}

SAMPLE_ID_REGEX_STR["sample_id"] = r"(?:(?:{})|(?:{}))".format(
    SAMPLE_ID_REGEX_STR["sample_id_non_control"],
    SAMPLE_ID_REGEX_STR["sample_id_control"]
)

LIBRARY_REGEX_STR = {
    "id_int": r"L\d{7}",
    "id_ext": r"L{}".format(SAMPLE_ID_REGEX_STR["sample_id"]),
    "year": r"(?:L|LPRJ)(\d{2})\d+"
}

LIBRARY_REGEX_STR["id"] = r"(?:{}|{})(?:{}|{})?".format(
    LIBRARY_REGEX_STR["id_int"],
    LIBRARY_REGEX_STR["id_ext"],
    EXPERIMENT_REGEX_STR["top_up"],                             # TODO - could a top_up/rerun exist?
    EXPERIMENT_REGEX_STR["rerun"]
)

SAMPLE_REGEX_OBJS = {
    # Sample ID: https://regex101.com/r/Z7fvHt/1
    "sample_id": re.compile(SAMPLE_ID_REGEX_STR["sample_id"]),
    # https://regex101.com/r/Z7fvHt/2
    "library_id": re.compile(LIBRARY_REGEX_STR["id"]),
    # https://regex101.com/r/Yf2t8E/2
    "unique_id_full_match": re.compile("{}_{}".format(SAMPLE_ID_REGEX_STR["sample_id"], LIBRARY_REGEX_STR["id"])),
    # https://regex101.com/r/Yf2t8E/3
    # Use brackets to capture the sample id and the library id
    "unique_id": re.compile("({})_({})".format(SAMPLE_ID_REGEX_STR["sample_id"], LIBRARY_REGEX_STR["id"])),
    # https://regex101.com/r/pkqI1n/1
    "topup": re.compile(EXPERIMENT_REGEX_STR["top_up"]),
    # https://regex101.com/r/nNPwQu/1
    "year": re.compile(LIBRARY_REGEX_STR["year"])
}

SAMPLESHEET_REGEX_STR = {
    "section_header": r"^\[(\S+)\](,+)?"
}

SAMPLESHEET_REGEX_OBJS = {
    # https://regex101.com/r/5nbe9I/1
    "section_header": re.compile(SAMPLESHEET_REGEX_STR["section_header"])
}

OVERRIDE_CYCLES_STR = {
    "cycles": r"(?:([INYU])(\d*))",
    "cycles_full_match": r"(?:[INYU]+(\d*))+",
    "indexes": r"((?:[I])(\d*))"
}

OVERRIDE_CYCLES_OBJS = {
    # https://regex101.com/r/U7bJUI/1
    "cycles": re.compile(OVERRIDE_CYCLES_STR["cycles"]),
    # https://regex101.com/r/U7bJUI/2
    "cycles_full_match": re.compile(OVERRIDE_CYCLES_STR["cycles_full_match"]),
    "indexes": re.compile(OVERRIDE_CYCLES_STR["indexes"])
}



"""
LOGS
"""
LOGGER_STYLE = "%(asctime)s - %(levelname)-8s - %(module)-25s - %(funcName)-40s : LineNo. %(lineno)-4d - %(message)s"


"""
INDEX DISTANCES
"""

MIN_INDEX_HAMMING_DISTANCE = 3

LOG_DIRECTORY = {
    "samplesheet_check" : "/tmp/samplesheet_check.log"
}


ADAPTERS_BY_KIT = {
    "truseq": {
        "adapter_read_1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
        "adapter_read_2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT"
    },
    "nextera": {
        "adapter_read_1": "CTGTCTCTTATACACATCT",
        "adapter_read_2": ""  # null is default and keeps current samplesheet, "" removes value
    },
    "pcr_free_tagmentation": {
        "adapter_read_1": "CTGTCTCTTATACACATCTCCGAGCCCACGAGAC+ATGTGTATAAGAGACA",
        "adapter_read_2": "CTGTCTCTTATACACATCTCGCAGGGGATAGTCAGATGACGCTGCCGACGA+ATGTGTATAAGAGACA"
    },
    "agilent_sureselect_qxt": {
        "adapter_read_1": "CTGTCTCTTGATCACA",
        "adapter_read_2": ""  # null is default and keeps current samplesheet, "" removes value
    },
}

V2_BCLCONVERT_BASESPACE_URN = "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7"
V2_BCLCONVERT_BASESPACE_SOFTWARE_VERSION = "4.2.7"

V2_SAMPLESHEET_BCLCONVERT_ADAPTER_SETTINGS_BY_ASSAY_TYPE = {
    # All 10X sample types
    "10X:.*": {
        "create_fastq_for_index_reads": True,
        "minimum_trimmed_read_length": 8,
        "mask_short_reads": 8,
        # Remove adapters as suggested here:
        # https://kb.10xgenomics.com/hc/en-us/articles/4424193781517-What-adapters-should-I-use-in-my-IEM-sample-sheet-
        "adapter_read_1": "",
        "adapter_read_2": ""
    },
    # TSO Assays
    "ctDNA:ctTSOv2": {
        "adapter_read_1": ADAPTERS_BY_KIT["nextera"]["adapter_read_1"],
        "adapter_read_2": ADAPTERS_BY_KIT["nextera"]["adapter_read_1"],  # Not a typo, both adapter reads are the same
        "adapter_behavior": "trim",
        "minimum_trimmed_read_length": 35,
        "mask_short_reads": 35,
    },
    "ctDNA:ctTSO|TSODNA|TSORNA": {
        "adapter_read_1": ADAPTERS_BY_KIT["truseq"]["adapter_read_1"],
        "adapter_read_2": ADAPTERS_BY_KIT["truseq"]["adapter_read_2"],
        "adapter_behavior": "trim",
        "minimum_trimmed_read_length": 35,
        "mask_short_reads": 35,
    },
    # PCR Free Tagementation Assays (rare)
    ".*:PCR-Free-Tagmentation": {
        "adapter_read_1": ADAPTERS_BY_KIT["pcr_free_tagmentation"]["adapter_read_1"],
        "adapter_read_2": ADAPTERS_BY_KIT["pcr_free_tagmentation"]["adapter_read_2"],
    },
    # Minimum Adapater Overlap for all samples set to 3
    ".*:.*": {
        "minimum_adapter_overlap": 3
    }
}

# Adapter settins can be set per sample
V2_ADAPTER_SETTINGS = [
    "barcode_mismatches_index1",
    "barcode_mismatches_index2",
    "adapter_read_1",
    "adapter_read_2",
    "adapter_behavior",
    "adapter_stringency"
]

# Data specific rows for v2
V2_DATA_ROWS = [
    "sample_id",
    "lane",
    "index",
    "index2",
    "sample_project",
    "sample_name",
    "library_prep_kit_name"
]

# Non-adapter settings that can be data settings
V2_SAMPLESHEET_DATA_SETTINGS = [
    "override_cycles"
]

# Samplesheet settings in the BCLConvert_Settings section
V2_SAMPLESHEET_GLOBAL_SETTINGS = {
    "minimum_trimmed_read_length": int,
    "minimum_adapter_overlap": int,
    "mask_short_reads": int,
    "override_cycles": int,
    "trim_umi": bool,
    "create_fastq_for_index_reads": bool,
    "no_lane_splitting": bool,
    "fastq_compression_format": FastqCompressionFormat,
    "find_adapters_with_indels": bool,
    "independent_index_collision_check": list,
}

# Add adapter settings to samplesheet settings
V2_SAMPLESHEET_DATA_SETTINGS.extend(V2_ADAPTER_SETTINGS)

# Add settings
V2_DATA_ROWS.extend(V2_SAMPLESHEET_DATA_SETTINGS)
