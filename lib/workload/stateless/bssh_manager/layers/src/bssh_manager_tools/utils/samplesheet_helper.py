#!/usr/bin/env python3

"""
Reads in a v2 samplesheet object from a file
"""
# Standard imports
import json
from io import StringIO
from pathlib import Path
from typing import Dict
from tempfile import NamedTemporaryFile

# UMCCR Libraries
from v2_samplesheet_maker.classes.samplesheet import SampleSheet
from wrapica.project_data import read_icav2_file_contents

# Logger
from ..utils.logger import get_logger


logger = get_logger()


def read_v2_samplesheet(project_id: str, data_id: str) -> Dict:
    """
    Given a v2 samplesheet path, read in the file as a v2 samplesheet (we first convert to json)

    :param project_id:
    :param data_id:

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

    with (
        NamedTemporaryFile(suffix='.csv') as input_csv,
        NamedTemporaryFile(suffix='.json') as output_json
    ):
        # Write the contents of the samplesheet to a temporary file
        read_icav2_file_contents(
            project_id=project_id,
            data_id=data_id,
            output_path=Path(input_csv.name)
        )

        # Read in the samplehseet from the temp file
        SampleSheet.read_from_samplesheet_csv(
            Path(input_csv.name)
        ).to_json(
            Path(output_json.name)
        )

        with open(output_json.name, 'r') as f:
            return json.loads(f.read())


# def get_library_assay_from_samplesheet_dict(library_id: str, samplesheet_dict: Dict):
#     """
#     Get the library assay from the samplesheet dict -
#     The library assay should be accessible from
#     Cloud_Data -> Sample_ID == Library_ID -> LibraryPrepKitName
#     :param library_id:
#     :param samplesheet_dict:
#     :return:
#     """
#     if 'Cloud_Data' not in samplesheet_dict.keys():
#         logger.warning("No Cloud_Data section in the samplesheet, could not get the library assay")
#         return None
#
#     cloud_data_df = pd.DataFrame(samplesheet_dict['Cloud_Data'])
#
#     # Get all matches to the library_id
#     library_df = cloud_data_df.query(f"Sample_ID == '{library_id}'")
#
#     if library_df.shape[0] == 0:
#         logger.warning(f"No matches to the library_id '{library_id}' in the Cloud_Data section of the samplesheet")
#         return None
#
#     library_kits = library_df["LibraryPrepKitName"].unique().tolist()
#
#     if len(library_kits) > 1:
#         logger.warning(f"Multiple library kits found for the library_id {library_id}: {library_kits}")
#         return None
#
#     return library_kits[0]
#
