#!/usr/bin/env python3

"""
Reads in a v2 samplesheet object from a file
"""

# Standard
import json
from io import StringIO
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Logger
from ..utils.logger import get_logger

logger = get_logger()


def read_v2_samplesheet(samplesheet_path: Path | StringIO) -> Dict:
    """
    Given a v2 samplesheet path, read in the file as a v2 samplesheet (we first convert to json)
    :param samplesheet_path:
    :return:

    /home/alexiswl/UMCCR/GitHub/v2-bclconvert-samplesheet-maker/venv/bin/python -m v2_samplesheet_maker.modules.v2_samplesheet_reader
    {
        "Header": {
            "FileFormatVersion": "2",
            "RunName": "Tsqn-NebRNA231113-MLeeSTR_16Nov23",
            "InstrumentType": "NovaSeq"
        },
        "Reads": {
            "Read1Cycles": "151",
            "Read2Cycles": "151",
            "Index1Cycles": "10",
            "Index2Cycles": "10"
        },
        "BCLConvert_Settings": {
            "MinimumTrimmedReadLength": "35",
            "MinimumAdapterOverlap": "3",
            "MaskShortReads": "35"
        },
        "BCLConvert_Data": [
            {
                "Lane": 1,
                "Sample_ID": "L2301368",
                "index": "GACTGAGTAG",
                "index2": "CACTATCAAC",
                "OverrideCycles": "U7N1Y143;I10;I10;U7N1Y143",
                "AdapterRead1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
                "AdapterRead2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
                "AdapterBehavior": "trim"
            },
            {
                "Lane": 1,
                "Sample_ID": "L2301369",
                "index": "AGTCAGACGA",
                "index2": "TGTCGCTGGT",
                "OverrideCycles": "U7N1Y143;I10;I10;U7N1Y143",
                "AdapterRead1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
                "AdapterRead2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
                "AdapterBehavior": "trim"
            },
           ...
        ],
        "Cloud_Settings": {
            "GeneratedVersion": "0.0.0",
            "Cloud_Workflow": "ica_workflow_1",
            "BCLConvert_Pipeline": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7"
        },
        "Cloud_Data": [
            {
                "Sample_ID": "L2301321",
                "LibraryName": "L2301321_CCGCGGTT_CTAGCGCT",
                "LibraryPrepKitName": "TsqSTR"
            },
            {
                "Sample_ID": "L2301322",
                "LibraryName": "L2301322_TTATAACC_TCGATATC",
                "LibraryPrepKitName": "TsqSTR"
            },
            ...
        ]
    }



    """

    # Part 1 - read in the samplesheet as a string
    if isinstance(samplesheet_path, Path):
        if not samplesheet_path.is_file():
            logger.error(f"Samplesheet path {samplesheet_path} is not a file")
            raise ValueError
        with open(samplesheet_path, 'r') as samplesheet_h:
            samplesheet_string_list = samplesheet_h.readlines()
    elif isinstance(samplesheet_path, StringIO):
        samplesheet_string_list = samplesheet_path.readlines()
    else:
        logger.error(f"Unknown type for samplesheet_path: {type(samplesheet_path)}")
        raise ValueError

    # Part 2 - assign each line to a header
    samplesheet_strings_by_header = {}

    header_name = None

    for line in samplesheet_string_list:
        if line.startswith('['):
            header_name = (line.strip().replace("[", "").replace("]", ""))
            samplesheet_strings_by_header[header_name] = []
            continue

        # Sample Line - check to make sure header_name is not None
        if header_name is None:
            logger.error("Got a non-header line before a header line in the samplesheet")
            raise ValueError

        # Don't add in blank lines
        if line.strip() == "":
            continue

        # Add the line to the values under the current header name
        samplesheet_strings_by_header[header_name].append(line.strip())

    # Part 3 - for each part, write out key value pairs or a data frame
    samplesheet_objects_by_header = {}

    for header_name, value_lines in samplesheet_strings_by_header.items():
        if header_name.lower().endswith("_data"):
            # This is the data section, which we will convert to a dataframe
            samplesheet_objects_by_header[header_name] = (
                json.loads(
                    pd.read_csv(
                        StringIO("\n".join(value_lines))
                    ).to_json(
                        orient='records'
                    )
                )
            )
        else:
            # This is a key value pair section
            samplesheet_objects_by_header[header_name] = {}
            for line in value_lines:
                key, value = line.split(",")
                samplesheet_objects_by_header[header_name][key] = value

    # Return the samplesheet as a dict
    return samplesheet_objects_by_header


def get_library_assay_from_samplesheet_dict(library_id: str, samplesheet_dict: Dict):
    """
    Get the library assay from the samplesheet dict -
    The library assay should be accessible from
    Cloud_Data -> Sample_ID == Library_ID -> LibraryPrepKitName
    :param library_id:
    :param samplesheet_dict:
    :return:
    """
    if 'Cloud_Data' not in samplesheet_dict.keys():
        logger.warning("No Cloud_Data section in the samplesheet, could not get the library assay")
        return None

    cloud_data_df = pd.DataFrame(samplesheet_dict['Cloud_Data'])

    # Get all matches to the library_id
    library_df = cloud_data_df.query(f"Sample_ID == '{library_id}'")

    if library_df.shape[0] == 0:
        logger.warning(f"No matches to the library_id '{library_id}' in the Cloud_Data section of the samplesheet")
        return None

    library_kits = library_df["LibraryPrepKitName"].unique().tolist()

    if len(library_kits) > 1:
        logger.warning(f"Multiple library kits found for the library_id {library_id}: {library_kits}")
        return None

    return library_kits[0]

