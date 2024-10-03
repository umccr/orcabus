#!/usr/bin/env python3

"""
Reads in a v2 samplesheet object from a file
"""
# Standard imports
from io import StringIO
from typing import Dict

from more_itertools import flatten
# UMCCR Libraries
from v2_samplesheet_maker.functions.v2_samplesheet_reader import v2_samplesheet_reader
from wrapica.project_data import read_icav2_file_contents_to_string

# Logger
import logging

# Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def read_v2_samplesheet(
        project_id: str,
        samplesheet_data_id: str,
        runinfo_data_id: str
) -> Dict:
    """
    Given a v2 samplesheet path, read in the file as a v2 samplesheet (we first convert to json)

    :param project_id:
    :param samplesheet_data_id:
    :param runinfo_data_id

    :return: A dictionary

    :Example:
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
    from ..runinfo import get_num_lanes_from_run_info

    v2_samplesheet_dict = v2_samplesheet_reader(
        StringIO(
            read_icav2_file_contents_to_string(
                project_id=project_id,
                data_id=samplesheet_data_id
            )
        )
    )

    # Get bclconvert data from the v2 samplesheet dict
    # And confirm that the lane column is present
    if 'lane' in v2_samplesheet_dict['bclconvert_data'][0].keys():
        # Return the samplesheet as is
        return v2_samplesheet_dict

    # Otherwise we read the runinfo file
    num_lanes = get_num_lanes_from_run_info(
        project_id=project_id,
        data_id=runinfo_data_id
    )

    # And now append the lane attribute to every
    v2_samplesheet_dict['bclconvert_data'] = flatten(
        map(
            lambda bclconvert_data_row_iter: list(
                map(
                    lambda lane_iter: {
                        **bclconvert_data_row_iter,
                        **{"lane": lane_iter + 1}
                    },
                    range(num_lanes)
                )
            ),
            v2_samplesheet_dict['bclconvert_data']
        ),
    )

    return v2_samplesheet_dict
