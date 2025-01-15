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

V2_CTTSO_VALID_INDEXES = [
    {"index_id": "UDP0001", "index": "GAACTGAGCG", "index2": "TCGTGGAGCG", "index_rev": "CGCTCAGTTC", "index2_rev": "CGCTCCACGA"},
    {"index_id": "UDP0002", "index": "AGGTCAGATA", "index2": "CTACAAGATA", "index_rev": "TATCTGACCT", "index2_rev": "TATCTTGTAG"},
    {"index_id": "UDP0003", "index": "CGTCTCATAT", "index2": "TATAGTAGCT", "index_rev": "ATATGAGACG", "index2_rev": "AGCTACTATA"},
    {"index_id": "UDP0004", "index": "ATTCCATAAG", "index2": "TGCCTGGTGG", "index_rev": "CTTATGGAAT", "index2_rev": "CCACCAGGCA"},
    {"index_id": "UDP0005", "index": "GACGAGATTA", "index2": "ACATTATCCT", "index_rev": "TAATCTCGTC", "index2_rev": "AGGATAATGT"},
    {"index_id": "UDP0006", "index": "AACATCGCGC", "index2": "GTCCACTTGT", "index_rev": "GCGCGATGTT", "index2_rev": "ACAAGTGGAC"},
    {"index_id": "UDP0007", "index": "CTAGTGCTCT", "index2": "TGGAACAGTA", "index_rev": "AGAGCACTAG", "index2_rev": "TACTGTTCCA"},
    {"index_id": "UDP0008", "index": "GATCAAGGCA", "index2": "CCTTGTTAAT", "index_rev": "TGCCTTGATC", "index2_rev": "ATTAACAAGG"},
    {"index_id": "UDP0009", "index": "GACTGAGTAG", "index2": "GTTGATAGTG", "index_rev": "CTACTCAGTC", "index2_rev": "CACTATCAAC"},
    {"index_id": "UDP0010", "index": "AGTCAGACGA", "index2": "ACCAGCGACA", "index_rev": "TCGTCTGACT", "index2_rev": "TGTCGCTGGT"},
    {"index_id": "UDP0011", "index": "CCGTATGTTC", "index2": "CATACACTGT", "index_rev": "GAACATACGG", "index2_rev": "ACAGTGTATG"},
    {"index_id": "UDP0012", "index": "GAGTCATAGG", "index2": "GTGTGGCGCT", "index_rev": "CCTATGACTC", "index2_rev": "AGCGCCACAC"},
    {"index_id": "UDP0013", "index": "CTTGCCATTA", "index2": "ATCACGAAGG", "index_rev": "TAATGGCAAG", "index2_rev": "CCTTCGTGAT"},
    {"index_id": "UDP0014", "index": "GAAGCGGCAC", "index2": "CGGCTCTACT", "index_rev": "GTGCCGCTTC", "index2_rev": "AGTAGAGCCG"},
    {"index_id": "UDP0015", "index": "TCCATTGCCG", "index2": "GAATGCACGA", "index_rev": "CGGCAATGGA", "index2_rev": "TCGTGCATTC"},
    {"index_id": "UDP0016", "index": "CGGTTACGGC", "index2": "AAGACTATAG", "index_rev": "GCCGTAACCG", "index2_rev": "CTATAGTCTT"},
    {"index_id": "UDP0017", "index": "GAGAATGGTT", "index2": "TCGGCAGCAA", "index_rev": "AACCATTCTC", "index2_rev": "TTGCTGCCGA"},
    {"index_id": "UDP0018", "index": "AGAGGCAACC", "index2": "CTAATGATGG", "index_rev": "GGTTGCCTCT", "index2_rev": "CCATCATTAG"},
    {"index_id": "UDP0019", "index": "CCATCATTAG", "index2": "GGTTGCCTCT", "index_rev": "CTAATGATGG", "index2_rev": "AGAGGCAACC"},
    {"index_id": "UDP0020", "index": "GATAGGCCGA", "index2": "CGCACATGGC", "index_rev": "TCGGCCTATC", "index2_rev": "GCCATGTGCG"},
    {"index_id": "UDP0021", "index": "ATGGTTGACT", "index2": "GGCCTGTCCT", "index_rev": "AGTCAACCAT", "index2_rev": "AGGACAGGCC"},
    {"index_id": "UDP0022", "index": "TATTGCGCTC", "index2": "CTGTGTTAGG", "index_rev": "GAGCGCAATA", "index2_rev": "CCTAACACAG"},
    {"index_id": "UDP0023", "index": "ACGCCTTGTT", "index2": "TAAGGAACGT", "index_rev": "AACAAGGCGT", "index2_rev": "ACGTTCCTTA"},
    {"index_id": "UDP0024", "index": "TTCTACATAC", "index2": "CTAACTGTAA", "index_rev": "GTATGTAGAA", "index2_rev": "TTACAGTTAG"},
    {"index_id": "UDP0025", "index": "AACCATAGAA", "index2": "GGCGAGATGG", "index_rev": "TTCTATGGTT", "index2_rev": "CCATCTCGCC"},
    {"index_id": "UDP0026", "index": "GGTTGCGAGG", "index2": "AATAGAGCAA", "index_rev": "CCTCGCAACC", "index2_rev": "TTGCTCTATT"},
    {"index_id": "UDP0027", "index": "TAAGCATCCA", "index2": "TCAATCCATT", "index_rev": "TGGATGCTTA", "index2_rev": "AATGGATTGA"},
    {"index_id": "UDP0028", "index": "ACCACGACAT", "index2": "TCGTATGCGG", "index_rev": "ATGTCGTGGT", "index2_rev": "CCGCATACGA"},
    {"index_id": "UDP0029", "index": "GCCGCACTCT", "index2": "TCCGACCTCG", "index_rev": "AGAGTGCGGC", "index2_rev": "CGAGGTCGGA"},
    {"index_id": "UDP0030", "index": "CCACCAGGCA", "index2": "CTTATGGAAT", "index_rev": "TGCCTGGTGG", "index2_rev": "ATTCCATAAG"},
    {"index_id": "UDP0031", "index": "GTGACACGCA", "index2": "GCTTACGGAC", "index_rev": "TGCGTGTCAC", "index2_rev": "GTCCGTAAGC"},
    {"index_id": "UDP0032", "index": "ACAGTGTATG", "index2": "GAACATACGG", "index_rev": "CATACACTGT", "index2_rev": "CCGTATGTTC"},
    {"index_id": "UDP0033", "index": "TGATTATACG", "index2": "GTCGATTACA", "index_rev": "CGTATAATCA", "index2_rev": "TGTAATCGAC"},
    {"index_id": "UDP0034", "index": "CAGCCGCGTA", "index2": "ACTAGCCGTG", "index_rev": "TACGCGGCTG", "index2_rev": "CACGGCTAGT"},
    {"index_id": "UDP0035", "index": "GGTAACTCGC", "index2": "AAGTTGGTGA", "index_rev": "GCGAGTTACC", "index2_rev": "TCACCAACTT"},
    {"index_id": "UDP0036", "index": "ACCGGCCGTA", "index2": "TGGCAATATT", "index_rev": "TACGGCCGGT", "index2_rev": "AATATTGCCA"},
    {"index_id": "UDP0037", "index": "TGTAATCGAC", "index2": "GATCACCGCG", "index_rev": "GTCGATTACA", "index2_rev": "CGCGGTGATC"},
    {"index_id": "UDP0038", "index": "GTGCAGACAG", "index2": "TACCATCCGT", "index_rev": "CTGTCTGCAC", "index2_rev": "ACGGATGGTA"},
    {"index_id": "UDP0039", "index": "CAATCGGCTG", "index2": "GCTGTAGGAA", "index_rev": "CAGCCGATTG", "index2_rev": "TTCCTACAGC"},
    {"index_id": "UDP0040", "index": "TATGTAGTCA", "index2": "CGCACTAATG", "index_rev": "TGACTACATA", "index2_rev": "CATTAGTGCG"},
    {"index_id": "UDP0041", "index": "ACTCGGCAAT", "index2": "GACAACTGAA", "index_rev": "ATTGCCGAGT", "index2_rev": "TTCAGTTGTC"},
    {"index_id": "UDP0042", "index": "GTCTAATGGC", "index2": "AGTGGTCAGG", "index_rev": "GCCATTAGAC", "index2_rev": "CCTGACCACT"},
    {"index_id": "UDP0043", "index": "CCATCTCGCC", "index2": "TTCTATGGTT", "index_rev": "GGCGAGATGG", "index2_rev": "AACCATAGAA"},
    {"index_id": "UDP0044", "index": "CTGCGAGCCA", "index2": "AATCCGGCCA", "index_rev": "TGGCTCGCAG", "index2_rev": "TGGCCGGATT"},
    {"index_id": "UDP0045", "index": "CGTTATTCTA", "index2": "CCATAAGGTT", "index_rev": "TAGAATAACG", "index2_rev": "AACCTTATGG"},
    {"index_id": "UDP0046", "index": "AGATCCATTA", "index2": "ATCTCTACCA", "index_rev": "TAATGGATCT", "index2_rev": "TGGTAGAGAT"},
    {"index_id": "UDP0047", "index": "GTCCTGGATA", "index2": "CGGTGGCGAA", "index_rev": "TATCCAGGAC", "index2_rev": "TTCGCCACCG"},
    {"index_id": "UDP0048", "index": "CAGTGGCACT", "index2": "TAACAATAGG", "index_rev": "AGTGCCACTG", "index2_rev": "CCTATTGTTA"},
    {"index_id": "UDP0049", "index": "AGTGTTGCAC", "index2": "CTGGTACACG", "index_rev": "GTGCAACACT", "index2_rev": "CGTGTACCAG"},
    {"index_id": "UDP0050", "index": "GACACCATGT", "index2": "TCAACGTGTA", "index_rev": "ACATGGTGTC", "index2_rev": "TACACGTTGA"},
    {"index_id": "UDP0051", "index": "CCTGTCTGTC", "index2": "ACTGTTGTGA", "index_rev": "GACAGACAGG", "index2_rev": "TCACAACAGT"},
    {"index_id": "UDP0052", "index": "TGATGTAAGA", "index2": "GTGCGTCCTT", "index_rev": "TCTTACATCA", "index2_rev": "AAGGACGCAC"},
    {"index_id": "UDP0053", "index": "GGAATTGTAA", "index2": "AGCACATCCT", "index_rev": "TTACAATTCC", "index2_rev": "AGGATGTGCT"},
    {"index_id": "UDP0054", "index": "GCATAAGCTT", "index2": "TTCCGTCGCA", "index_rev": "AAGCTTATGC", "index2_rev": "TGCGACGGAA"},
    {"index_id": "UDP0055", "index": "CTGAGGAATA", "index2": "CTTAACCACT", "index_rev": "TATTCCTCAG", "index2_rev": "AGTGGTTAAG"},
    {"index_id": "UDP0056", "index": "AACGCACGAG", "index2": "GCCTCGGATA", "index_rev": "CTCGTGCGTT", "index2_rev": "TATCCGAGGC"},
    {"index_id": "UDP0057", "index": "TCTATCCTAA", "index2": "CGTCGACTGG", "index_rev": "TTAGGATAGA", "index2_rev": "CCAGTCGACG"},
    {"index_id": "UDP0058", "index": "CTCGCTTCGG", "index2": "TACTAGTCAA", "index_rev": "CCGAAGCGAG", "index2_rev": "TTGACTAGTA"},
    {"index_id": "UDP0059", "index": "CTGTTGGTCC", "index2": "ATAGACCGTT", "index_rev": "GGACCAACAG", "index2_rev": "AACGGTCTAT"},
    {"index_id": "UDP0060", "index": "TTACCTGGAA", "index2": "ACAGTTCCAG", "index_rev": "TTCCAGGTAA", "index2_rev": "CTGGAACTGT"},
    {"index_id": "UDP0061", "index": "TGGCTAATCA", "index2": "AGGCATGTAG", "index_rev": "TGATTAGCCA", "index2_rev": "CTACATGCCT"},
    {"index_id": "UDP0062", "index": "AACACTGTTA", "index2": "GCAAGTCTCA", "index_rev": "TAACAGTGTT", "index2_rev": "TGAGACTTGC"},
    {"index_id": "UDP0063", "index": "ATTGCGCGGT", "index2": "TTGGCTCCGC", "index_rev": "ACCGCGCAAT", "index2_rev": "GCGGAGCCAA"},
    {"index_id": "UDP0064", "index": "TGGCGCGAAC", "index2": "AACTGATACT", "index_rev": "GTTCGCGCCA", "index2_rev": "AGTATCAGTT"},
    {"index_id": "UDP0065", "index": "TAATGTGTCT", "index2": "GTAAGGCATA", "index_rev": "AGACACATTA", "index2_rev": "TATGCCTTAC"},
    {"index_id": "UDP0066", "index": "ATACCAACGC", "index2": "AATTGCTGCG", "index_rev": "GCGTTGGTAT", "index2_rev": "CGCAGCAATT"},
    {"index_id": "UDP0067", "index": "AGGATGTGCT", "index2": "TTACAATTCC", "index_rev": "AGCACATCCT", "index2_rev": "GGAATTGTAA"},
    {"index_id": "UDP0068", "index": "CACGGAACAA", "index2": "AACCTAGCAC", "index_rev": "TTGTTCCGTG", "index2_rev": "GTGCTAGGTT"},
    {"index_id": "UDP0069", "index": "TGGAGTACTT", "index2": "TCTGTGTGGA", "index_rev": "AAGTACTCCA", "index2_rev": "TCCACACAGA"},
    {"index_id": "UDP0070", "index": "GTATTGACGT", "index2": "GGAATTCCAA", "index_rev": "ACGTCAATAC", "index2_rev": "TTGGAATTCC"},
    {"index_id": "UDP0071", "index": "CTTGTACACC", "index2": "AAGCGCGCTT", "index_rev": "GGTGTACAAG", "index2_rev": "AAGCGCGCTT"},
    {"index_id": "UDP0072", "index": "ACACAGGTGG", "index2": "TGAGCGTTGT", "index_rev": "CCACCTGTGT", "index2_rev": "ACAACGCTCA"},
    {"index_id": "UDP0073", "index": "CCTGCGGAAC", "index2": "ATCATAGGCT", "index_rev": "GTTCCGCAGG", "index2_rev": "AGCCTATGAT"},
    {"index_id": "UDP0074", "index": "TTCATAAGGT", "index2": "TGTTAGAAGG", "index_rev": "ACCTTATGAA", "index2_rev": "CCTTCTAACA"},
    {"index_id": "UDP0075", "index": "CTCTGCAGCG", "index2": "GATGGATGTA", "index_rev": "CGCTGCAGAG", "index2_rev": "TACATCCATC"},
    {"index_id": "UDP0076", "index": "CTGACTCTAC", "index2": "ACGGCCGTCA", "index_rev": "GTAGAGTCAG", "index2_rev": "TGACGGCCGT"},
    {"index_id": "UDP0077", "index": "TCTGGTATCC", "index2": "CGTTGCTTAC", "index_rev": "GGATACCAGA", "index2_rev": "GTAAGCAACG"},
    {"index_id": "UDP0078", "index": "CATTAGTGCG", "index2": "TGACTACATA", "index_rev": "CGCACTAATG", "index2_rev": "TATGTAGTCA"},
    {"index_id": "UDP0079", "index": "ACGGTCAGGA", "index2": "CGGCCTCGTT", "index_rev": "TCCTGACCGT", "index2_rev": "AACGAGGCCG"},
    {"index_id": "UDP0080", "index": "GGCAAGCCAG", "index2": "CAAGCATCCG", "index_rev": "CTGGCTTGCC", "index2_rev": "CGGATGCTTG"},
    {"index_id": "UDP0081", "index": "TGTCGCTGGT", "index2": "TCGTCTGACT", "index_rev": "ACCAGCGACA", "index2_rev": "AGTCAGACGA"},
    {"index_id": "UDP0082", "index": "ACCGTTACAA", "index2": "CTCATAGCGA", "index_rev": "TTGTAACGGT", "index2_rev": "TCGCTATGAG"},
    {"index_id": "UDP0083", "index": "TATGCCTTAC", "index2": "AGACACATTA", "index_rev": "GTAAGGCATA", "index2_rev": "TAATGTGTCT"},
    {"index_id": "UDP0084", "index": "ACAAGTGGAC", "index2": "GCGCGATGTT", "index_rev": "GTCCACTTGT", "index2_rev": "AACATCGCGC"},
    {"index_id": "UDP0085", "index": "TGGTACCTAA", "index2": "CATGAGTACT", "index_rev": "TTAGGTACCA", "index2_rev": "AGTACTCATG"},
    {"index_id": "UDP0086", "index": "TTGGAATTCC", "index2": "ACGTCAATAC", "index_rev": "GGAATTCCAA", "index2_rev": "GTATTGACGT"},
    {"index_id": "UDP0087", "index": "CCTCTACATG", "index2": "GATACCTCCT", "index_rev": "CATGTAGAGG", "index2_rev": "AGGAGGTATC"},
    {"index_id": "UDP0088", "index": "GGAGCGTGTA", "index2": "ATCCGTAAGT", "index_rev": "TACACGCTCC", "index2_rev": "ACTTACGGAT"},
    {"index_id": "UDP0089", "index": "GTCCGTAAGC", "index2": "CGTGTATCTT", "index_rev": "GCTTACGGAC", "index2_rev": "AAGATACACG"},
    {"index_id": "UDP0090", "index": "ACTTCAAGCG", "index2": "GAACCATGAA", "index_rev": "CGCTTGAAGT", "index2_rev": "TTCATGGTTC"},
    {"index_id": "UDP0091", "index": "TCAGAAGGCG", "index2": "GGCCATCATA", "index_rev": "CGCCTTCTGA", "index2_rev": "TATGATGGCC"},
    {"index_id": "UDP0092", "index": "GCGTTGGTAT", "index2": "ACATACTTCC", "index_rev": "ATACCAACGC", "index2_rev": "GGAAGTATGT"},
    {"index_id": "UDP0093", "index": "ACATATCCAG", "index2": "TATGTGCAAT", "index_rev": "CTGGATATGT", "index2_rev": "ATTGCACATA"},
    {"index_id": "UDP0094", "index": "TCATAGATTG", "index2": "GATTAAGGTG", "index_rev": "CAATCTATGA", "index2_rev": "CACCTTAATC"},
    {"index_id": "UDP0095", "index": "GTATTCCACC", "index2": "ATGTAGACAA", "index_rev": "GGTGGAATAC", "index2_rev": "TTGTCTACAT"},
    {"index_id": "UDP0096", "index": "CCTCCGTCCA", "index2": "CACATCGGTG", "index_rev": "TGGACGGAGG", "index2_rev": "CACCGATGTG"},
    {"index_id": "UDP0097", "index": "TGCCGGTCAG", "index2": "CCTGATACAA", "index_rev": "CTGACCGGCA", "index2_rev": "TTGTATCAGG"},
    {"index_id": "UDP0098", "index": "CACTCAATTC", "index2": "TTAAGTTGTG", "index_rev": "GAATTGAGTG", "index2_rev": "CACAACTTAA"},
    {"index_id": "UDP0099", "index": "TCTCACACGC", "index2": "CGGACAGTGA", "index_rev": "GCGTGTGAGA", "index2_rev": "TCACTGTCCG"},
    {"index_id": "UDP0100", "index": "TCAATGGAGA", "index2": "GCACTACAAC", "index_rev": "TCTCCATTGA", "index2_rev": "GTTGTAGTGC"},
    {"index_id": "UDP0101", "index": "ATATGCATGT", "index2": "TGGTGCCTGG", "index_rev": "ACATGCATAT", "index2_rev": "CCAGGCACCA"},
    {"index_id": "UDP0102", "index": "ATGGCGCCTG", "index2": "TCCACGGCCT", "index_rev": "CAGGCGCCAT", "index2_rev": "AGGCCGTGGA"},
    {"index_id": "UDP0103", "index": "TCCGTTATGT", "index2": "TTGTAGTGTA", "index_rev": "ACATAACGGA", "index2_rev": "TACACTACAA"},
    {"index_id": "UDP0104", "index": "GGTCTATTAA", "index2": "CCACGACACG", "index_rev": "TTAATAGACC", "index2_rev": "CGTGTCGTGG"},
    {"index_id": "UDP0105", "index": "CAGCAATCGT", "index2": "TGTGATGTAT", "index_rev": "ACGATTGCTG", "index2_rev": "ATACATCACA"},
    {"index_id": "UDP0106", "index": "TTCTGTAGAA", "index2": "GAGCGCAATA", "index_rev": "TTCTACAGAA", "index2_rev": "TATTGCGCTC"},
    {"index_id": "UDP0107", "index": "GAACGCAATA", "index2": "ATCTTACTGT", "index_rev": "TATTGCGTTC", "index2_rev": "ACAGTAAGAT"},
    {"index_id": "UDP0108", "index": "AGTACTCATG", "index2": "ATGTCGTGGT", "index_rev": "CATGAGTACT", "index2_rev": "ACCACGACAT"},
    {"index_id": "UDP0109", "index": "GGTAGAATTA", "index2": "GTAGCCATCA", "index_rev": "TAATTCTACC", "index2_rev": "TGATGGCTAC"},
    {"index_id": "UDP0110", "index": "TAATTAGCGT", "index2": "TGGTTAAGAA", "index_rev": "ACGCTAATTA", "index2_rev": "TTCTTAACCA"},
    {"index_id": "UDP0111", "index": "ATTAACAAGG", "index2": "TGTTGTTCGT", "index_rev": "CCTTGTTAAT", "index2_rev": "ACGAACAACA"},
    {"index_id": "UDP0112", "index": "TGATGGCTAC", "index2": "CCAACAACAT", "index_rev": "GTAGCCATCA", "index2_rev": "ATGTTGTTGG"},
    {"index_id": "UDP0113", "index": "GAATTACAAG", "index2": "ACCGGCTCAG", "index_rev": "CTTGTAATTC", "index2_rev": "CTGAGCCGGT"},
    {"index_id": "UDP0114", "index": "TAGAATTGGA", "index2": "GTTAATCTGA", "index_rev": "TCCAATTCTA", "index2_rev": "TCAGATTAAC"},
    {"index_id": "UDP0115", "index": "AGGCAGCTCT", "index2": "CGGCTAACGT", "index_rev": "AGAGCTGCCT", "index2_rev": "ACGTTAGCCG"},
    {"index_id": "UDP0116", "index": "ATCGGCGAAG", "index2": "TCCAAGAATT", "index_rev": "CTTCGCCGAT", "index2_rev": "AATTCTTGGA"},
    {"index_id": "UDP0117", "index": "CCGTGACCGA", "index2": "CCGAACGTTG", "index_rev": "TCGGTCACGG", "index2_rev": "CAACGTTCGG"},
    {"index_id": "UDP0118", "index": "ATACTTGTTC", "index2": "TAACCGCCGA", "index_rev": "GAACAAGTAT", "index2_rev": "TCGGCGGTTA"},
    {"index_id": "UDP0119", "index": "TCCGCCAATT", "index2": "CTCCGTGCTG", "index_rev": "AATTGGCGGA", "index2_rev": "CAGCACGGAG"},
    {"index_id": "UDP0120", "index": "AGGACAGGCC", "index2": "CATTCCAGCT", "index_rev": "GGCCTGTCCT", "index2_rev": "AGCTGGAATG"},
    {"index_id": "UDP0121", "index": "AGAGAACCTA", "index2": "GGTTATGCTA", "index_rev": "TAGGTTCTCT", "index2_rev": "TAGCATAACC"},
    {"index_id": "UDP0122", "index": "GATATTGTGT", "index2": "ACCACACGGT", "index_rev": "ACACAATATC", "index2_rev": "ACCGTGTGGT"},
    {"index_id": "UDP0123", "index": "CGTACAGGAA", "index2": "TAGGTTCTCT", "index_rev": "TTCCTGTACG", "index2_rev": "AGAGAACCTA"},
    {"index_id": "UDP0124", "index": "CTGCGTTACC", "index2": "TATGGCTCGA", "index_rev": "GGTAACGCAG", "index2_rev": "TCGAGCCATA"},
    {"index_id": "UDP0125", "index": "AGGCCGTGGA", "index2": "CTCGTGCGTT", "index_rev": "TCCACGGCCT", "index2_rev": "AACGCACGAG"},
    {"index_id": "UDP0126", "index": "AGGAGGTATC", "index2": "CCAGTTGGCA", "index_rev": "GATACCTCCT", "index2_rev": "TGCCAACTGG"},
    {"index_id": "UDP0127", "index": "GCTGACGTTG", "index2": "TGTTCGCATT", "index_rev": "CAACGTCAGC", "index2_rev": "AATGCGAACA"},
    {"index_id": "UDP0128", "index": "CTAATAACCG", "index2": "AACCGCATCG", "index_rev": "CGGTTATTAG", "index2_rev": "CGATGCGGTT"},
    {"index_id": "UDP0129", "index": "TCTAGGCGCG", "index2": "CGAAGGTTAA", "index_rev": "CGCGCCTAGA", "index2_rev": "TTAACCTTCG"},
    {"index_id": "UDP0130", "index": "ATAGCCAAGA", "index2": "AGTGCCACTG", "index_rev": "TCTTGGCTAT", "index2_rev": "CAGTGGCACT"},
    {"index_id": "UDP0131", "index": "TTCGGTGTGA", "index2": "GAACAAGTAT", "index_rev": "TCACACCGAA", "index2_rev": "ATACTTGTTC"},
    {"index_id": "UDP0132", "index": "ATGTAACGTT", "index2": "ACGATTGCTG", "index_rev": "AACGTTACAT", "index2_rev": "CAGCAATCGT"},
    {"index_id": "UDP0133", "index": "AACGAGGCCG", "index2": "ATACCTGGAT", "index_rev": "CGGCCTCGTT", "index2_rev": "ATCCAGGTAT"},
    {"index_id": "UDP0134", "index": "TGGTGTTATG", "index2": "TCCAATTCTA", "index_rev": "CATAACACCA", "index2_rev": "TAGAATTGGA"},
    {"index_id": "UDP0135", "index": "TGGCCTCTGT", "index2": "TGAGACAGCG", "index_rev": "ACAGAGGCCA", "index2_rev": "CGCTGTCTCA"},
    {"index_id": "UDP0136", "index": "CCAGGCACCA", "index2": "ACGCTAATTA", "index_rev": "TGGTGCCTGG", "index2_rev": "TAATTAGCGT"},
    {"index_id": "UDP0137", "index": "CCGGTTCCTA", "index2": "TATATTCGAG", "index_rev": "TAGGAACCGG", "index2_rev": "CTCGAATATA"},
    {"index_id": "UDP0138", "index": "GGCCAATATT", "index2": "CGGTCCGATA", "index_rev": "AATATTGGCC", "index2_rev": "TATCGGACCG"},
    {"index_id": "UDP0139", "index": "GAATACCTAT", "index2": "ACAATAGAGT", "index_rev": "ATAGGTATTC", "index2_rev": "ACTCTATTGT"},
    {"index_id": "UDP0140", "index": "TACGTGAAGG", "index2": "CGGTTATTAG", "index_rev": "CCTTCACGTA", "index2_rev": "CTAATAACCG"},
    {"index_id": "UDP0141", "index": "CTTATTGGCC", "index2": "GATAACAAGT", "index_rev": "GGCCAATAAG", "index2_rev": "ACTTGTTATC"},
    {"index_id": "UDP0142", "index": "ACAACTACTG", "index2": "AGTTATCACA", "index_rev": "CAGTAGTTGT", "index2_rev": "TGTGATAACT"},
    {"index_id": "UDP0143", "index": "GTTGGATGAA", "index2": "TTCCAGGTAA", "index_rev": "TTCATCCAAC", "index2_rev": "TTACCTGGAA"},
    {"index_id": "UDP0144", "index": "AATCCAATTG", "index2": "CATGTAGAGG", "index_rev": "CAATTGGATT", "index2_rev": "CCTCTACATG"},
    {"index_id": "UDP0145", "index": "TATGATGGCC", "index2": "GATTGTCATA", "index_rev": "GGCCATCATA", "index2_rev": "TATGACAATC"},
    {"index_id": "UDP0146", "index": "CGCAGCAATT", "index2": "ATTCCGCTAT", "index_rev": "AATTGCTGCG", "index2_rev": "ATAGCGGAAT"},
    {"index_id": "UDP0147", "index": "ACGTTCCTTA", "index2": "GACCGCTGTG", "index_rev": "TAAGGAACGT", "index2_rev": "CACAGCGGTC"},
    {"index_id": "UDP0148", "index": "CCGCGTATAG", "index2": "TAGGAACCGG", "index_rev": "CTATACGCGG", "index2_rev": "CCGGTTCCTA"},
    {"index_id": "UDP0149", "index": "GATTCTGAAT", "index2": "AGCGGTGGAC", "index_rev": "ATTCAGAATC", "index2_rev": "GTCCACCGCT"},
    {"index_id": "UDP0150", "index": "TAGAGAATAC", "index2": "TATAGATTCG", "index_rev": "GTATTCTCTA", "index2_rev": "CGAATCTATA"},
    {"index_id": "UDP0151", "index": "TTGTATCAGG", "index2": "ACAGAGGCCA", "index_rev": "CCTGATACAA", "index2_rev": "TGGCCTCTGT"},
    {"index_id": "UDP0152", "index": "CACAGCGGTC", "index2": "ATTCCTATTG", "index_rev": "GACCGCTGTG", "index2_rev": "CAATAGGAAT"},
    {"index_id": "UDP0153", "index": "CCACGCTGAA", "index2": "TATTCCTCAG", "index_rev": "TTCAGCGTGG", "index2_rev": "CTGAGGAATA"},
    {"index_id": "UDP0154", "index": "GTTCGGAGTT", "index2": "CGCCTTCTGA", "index_rev": "AACTCCGAAC", "index2_rev": "TCAGAAGGCG"},
    {"index_id": "UDP0155", "index": "ATAGCGGAAT", "index2": "GCGCAGAGTA", "index_rev": "ATTCCGCTAT", "index2_rev": "TACTCTGCGC"},
    {"index_id": "UDP0156", "index": "GCAATATTCA", "index2": "GGCGCCAATT", "index_rev": "TGAATATTGC", "index2_rev": "AATTGGCGCC"},
    {"index_id": "UDP0157", "index": "CTAGATTGCG", "index2": "AGATATGGCG", "index_rev": "CGCAATCTAG", "index2_rev": "CGCCATATCT"},
    {"index_id": "UDP0158", "index": "CGATGCGGTT", "index2": "CCTGCTTGGT", "index_rev": "AACCGCATCG", "index2_rev": "ACCAAGCAGG"},
    {"index_id": "UDP0159", "index": "TCCGGACTAG", "index2": "GACGAACAAT", "index_rev": "CTAGTCCGGA", "index2_rev": "ATTGTTCGTC"},
    {"index_id": "UDP0160", "index": "GTGACGGAGC", "index2": "TGGCGGTCCA", "index_rev": "GCTCCGTCAC", "index2_rev": "TGGACCGCCA"},
    {"index_id": "UDP0161", "index": "AATTCCATCT", "index2": "CTTCAGTTAC", "index_rev": "AGATGGAATT", "index2_rev": "GTAACTGAAG"},
    {"index_id": "UDP0162", "index": "TTAACGGTGT", "index2": "TCCTGACCGT", "index_rev": "ACACCGTTAA", "index2_rev": "ACGGTCAGGA"},
    {"index_id": "UDP0163", "index": "ACTTGTTATC", "index2": "CGCGCCTAGA", "index_rev": "GATAACAAGT", "index2_rev": "TCTAGGCGCG"},
    {"index_id": "UDP0164", "index": "CGTGTACCAG", "index2": "AGGATAAGTT", "index_rev": "CTGGTACACG", "index2_rev": "AACTTATCCT"},
    {"index_id": "UDP0165", "index": "TTAACCTTCG", "index2": "AGGCCAGACA", "index_rev": "CGAAGGTTAA", "index2_rev": "TGTCTGGCCT"},
    {"index_id": "UDP0166", "index": "CATATGCGAT", "index2": "CCTTGAACGG", "index_rev": "ATCGCATATG", "index2_rev": "CCGTTCAAGG"},
    {"index_id": "UDP0167", "index": "AGCCTATGAT", "index2": "CACCACCTAC", "index_rev": "ATCATAGGCT", "index2_rev": "GTAGGTGGTG"},
    {"index_id": "UDP0168", "index": "TATGACAATC", "index2": "TTGCTTGTAT", "index_rev": "GATTGTCATA", "index2_rev": "ATACAAGCAA"},
    {"index_id": "UDP0169", "index": "ATGTTGTTGG", "index2": "CAATCTATGA", "index_rev": "CCAACAACAT", "index2_rev": "TCATAGATTG"},
    {"index_id": "UDP0170", "index": "GCACCACCAA", "index2": "TGGTACTGAT", "index_rev": "TTGGTGGTGC", "index2_rev": "ATCAGTACCA"},
    {"index_id": "UDP0171", "index": "AGGCGTTCGC", "index2": "TTCATCCAAC", "index_rev": "GCGAACGCCT", "index2_rev": "GTTGGATGAA"},
    {"index_id": "UDP0172", "index": "CCTCCGGTTG", "index2": "CATAACACCA", "index_rev": "CAACCGGAGG", "index2_rev": "TGGTGTTATG"},
    {"index_id": "UDP0173", "index": "GTCCACCGCT", "index2": "TCCTATTAGC", "index_rev": "AGCGGTGGAC", "index2_rev": "GCTAATAGGA"},
    {"index_id": "UDP0174", "index": "ATTGTTCGTC", "index2": "TCTCTAGATT", "index_rev": "GACGAACAAT", "index2_rev": "AATCTAGAGA"},
    {"index_id": "UDP0175", "index": "GGACCAGTGG", "index2": "CGCGAGCCTA", "index_rev": "CCACTGGTCC", "index2_rev": "TAGGCTCGCG"},
    {"index_id": "UDP0176", "index": "CCTTCTAACA", "index2": "GATAAGCTCT", "index_rev": "TGTTAGAAGG", "index2_rev": "AGAGCTTATC"},
    {"index_id": "UDP0177", "index": "CTCGAATATA", "index2": "GAGATGTCGA", "index_rev": "TATATTCGAG", "index2_rev": "TCGACATCTC"},
    {"index_id": "UDP0178", "index": "GATCGTCGCG", "index2": "CTGGATATGT", "index_rev": "CGCGACGATC", "index2_rev": "ACATATCCAG"},
    {"index_id": "UDP0179", "index": "TATCCGAGGC", "index2": "GGCCAATAAG", "index_rev": "GCCTCGGATA", "index2_rev": "CTTATTGGCC"},
    {"index_id": "UDP0180", "index": "CGCTGTCTCA", "index2": "ATTACTCACC", "index_rev": "TGAGACAGCG", "index2_rev": "GGTGAGTAAT"},
    {"index_id": "UDP0181", "index": "AATGCGAACA", "index2": "AATTGGCGGA", "index_rev": "TGTTCGCATT", "index2_rev": "TCCGCCAATT"},
    {"index_id": "UDP0182", "index": "AATTCTTGGA", "index2": "TTGTCAACTT", "index_rev": "TCCAAGAATT", "index2_rev": "AAGTTGACAA"},
    {"index_id": "UDP0183", "index": "TTCCTACAGC", "index2": "GGCGAATTCT", "index_rev": "GCTGTAGGAA", "index2_rev": "AGAATTCGCC"},
    {"index_id": "UDP0184", "index": "ATCCAGGTAT", "index2": "CAACGTCAGC", "index_rev": "ATACCTGGAT", "index2_rev": "GCTGACGTTG"},
    {"index_id": "UDP0185", "index": "ACGGTCCAAC", "index2": "TCTTACATCA", "index_rev": "GTTGGACCGT", "index2_rev": "TGATGTAAGA"},
    {"index_id": "UDP0186", "index": "GTAACTTGGT", "index2": "CGCCATACCT", "index_rev": "ACCAAGTTAC", "index2_rev": "AGGTATGGCG"},
    {"index_id": "UDP0187", "index": "AGCGCCACAC", "index2": "CTAATGTCTT", "index_rev": "GTGTGGCGCT", "index2_rev": "AAGACATTAG"},
    {"index_id": "UDP0188", "index": "TGCTACTGCC", "index2": "CAACCGGAGG", "index_rev": "GGCAGTAGCA", "index2_rev": "CCTCCGGTTG"},
    {"index_id": "UDP0189", "index": "CAACACCGCA", "index2": "GGCAGTAGCA", "index_rev": "TGCGGTGTTG", "index2_rev": "TGCTACTGCC"},
    {"index_id": "UDP0190", "index": "CACCTTAATC", "index2": "TTAGGATAGA", "index_rev": "GATTAAGGTG", "index2_rev": "TCTATCCTAA"},
    {"index_id": "UDP0191", "index": "TTGAATGTTG", "index2": "CGCAATCTAG", "index_rev": "CAACATTCAA", "index2_rev": "CTAGATTGCG"},
    {"index_id": "UDP0192", "index": "CCGGTAACAC", "index2": "GAGTTGTACT", "index_rev": "GTGTTACCGG", "index2_rev": "AGTACAACTC"}
]