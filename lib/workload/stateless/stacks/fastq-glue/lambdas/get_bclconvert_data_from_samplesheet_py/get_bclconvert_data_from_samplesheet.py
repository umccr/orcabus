#!/usr/bin/env python3

"""
Get the bclconvert data from the samplesheet

Given the inputs

sampleId and sampleSheetUri,

1. Pull the sample sheet from S3
2. Parse in the samplesheet as a json object
3. Get the bclconvert_data section and filter only the objects where sample_id is equal to sampleId

"""

# Imports
import typing
from typing import Dict, List, Optional, Union
import re


from sequence_tools import (
    get_sequence_object_from_instrument_run_id,
    get_sample_sheet_from_orcabus_id
)


def get_cycle_count_from_bclconvert_data_row(bclconvert_data_row: Dict[str, str]) -> Optional[int]:
    if "overrideCycles" in bclconvert_data_row:
        override_cycles = bclconvert_data_row['overrideCycles']
        return get_cycle_count_from_override_cycles(override_cycles)
    return None


def get_sample_bclconvert_data_from_v2_samplesheet(
        samplesheet: Dict,
        sample_id: str,
        global_cycle_count: int
) -> List[Dict[str, Union[str, int]]]:
    # Get the bclconvert data from the samplesheet
    # Return only the rows of the bclconvert data section where sample_id is equal to sampleId
    return(
        list(map(
            lambda bclconvert_row_iter_: {
                "libraryId": bclconvert_row_iter_['sampleId'],
                "index": bclconvert_row_iter_['index'] + ("+" + bclconvert_row_iter_['index2'] if bclconvert_row_iter_['index2'] else ""),
                "lane": int(bclconvert_row_iter_['lane']),
                "cycleCount": (
                    get_cycle_count_from_bclconvert_data_row(bclconvert_row_iter_)
                    if get_cycle_count_from_bclconvert_data_row(bclconvert_row_iter_) is not None
                    else global_cycle_count
                )
            },
            list(filter(
                lambda bclconvert_row_iter_: bclconvert_row_iter_['sampleId'] == sample_id,
                samplesheet['bclconvertData']
            ))
        ))
    )


def get_cycle_count_from_override_cycles(override_cycles: str) -> int:
    read_cycle_regex_match = re.findall("(?:[yY])([0-9]+)", override_cycles)
    if read_cycle_regex_match is None or len(read_cycle_regex_match) == 0:
        raise ValueError("Invalid override_cycles format")
    if len(read_cycle_regex_match) == 1:
        return int(read_cycle_regex_match[0])
    return int(read_cycle_regex_match[0]) + int(read_cycle_regex_match[1])


def get_global_cycle_count(samplesheet: Dict) -> int:
    if samplesheet['bclconvertSettings'].get("overrideCycles") is not None:
        override_cycles = samplesheet['bclconvertSettings']['overrideCycles']
        return get_cycle_count_from_override_cycles(override_cycles)
    return samplesheet['reads']['read1Cycles'] + samplesheet['reads'].get('read2Cycles', None)


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Given a samplesheet uri and a list of library ids,
    Download the samplesheet, get the bclconvert data section
    and return only the rows where sample_id is equal to libraryId
    :param event:
    :param context:
    :return:
    """

    # Get the sample id and samplesheet uri from the event
    library_id_list = event['libraryIdList']
    instrument_run_id = event['instrumentRunId']

    # Get the sequence orcabus id

    # Read the samplesheet
    sequence_orcabus_id = get_sequence_object_from_instrument_run_id(instrument_run_id)['orcabusId']

    samplesheet: Dict = get_sample_sheet_from_orcabus_id(sequence_orcabus_id)['sampleSheetContent']

    # Get override cycles from the samplesheet settings section
    global_cycle_count = get_global_cycle_count(samplesheet)

    # Get the bclconvert data from the samplesheet
    bclconvert_data_by_library = list(map(
        lambda library_id_iter_: {
            "libraryId": library_id_iter_,
            "bclConvertData": get_sample_bclconvert_data_from_v2_samplesheet(
                samplesheet=samplesheet,
                sample_id=library_id_iter_,
                global_cycle_count=global_cycle_count
            )
        },
        library_id_list
    ))

    # Return the bclconvert data
    return {
        'bclConvertDataByLibrary': bclconvert_data_by_library
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(json.dumps(
#         handler(
#             {
#                 "instrumentRunId": "250307_A00130_0360_BHCLW2DSXF",
#                 "libraryIdList": [
#                     "L2500185",
#                     "L2500181",
#                     "L2500175",
#                     "L2500176",
#                     "L2500180",
#                 ]
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "bclConvertDataByLibrary": [
#     #         {
#     #             "libraryId": "L2500185",
#     #             "bclConvertData": [
#     #                 {
#     #                     "libraryId": "L2500185",
#     #                     "index": "TTAATCAG+CTTCGCCT",
#     #                     "lane": 4,
#     #                     "cycleCount": 286
#     #                 }
#     #             ]
#     #         },
#     #         {
#     #             "libraryId": "L2500181",
#     #             "bclConvertData": [
#     #                 {
#     #                     "libraryId": "L2500181",
#     #                     "index": "GGCTTACT+AGGGAAAG",
#     #                     "lane": 2,
#     #                     "cycleCount": 302
#     #                 }
#     #             ]
#     #         },
#     #         {
#     #             "libraryId": "L2500175",
#     #             "bclConvertData": [
#     #                 {
#     #                     "libraryId": "L2500175",
#     #                     "index": "AACTGTAG+TGCGGCGT",
#     #                     "lane": 3,
#     #                     "cycleCount": 302
#     #                 },
#     #                 {
#     #                     "libraryId": "L2500175",
#     #                     "index": "AACTGTAG+TGCGGCGT",
#     #                     "lane": 4,
#     #                     "cycleCount": 302
#     #                 }
#     #             ]
#     #         },
#     #         {
#     #             "libraryId": "L2500176",
#     #             "bclConvertData": [
#     #                 {
#     #                     "libraryId": "L2500176",
#     #                     "index": "GGTCACGA+CATAATAC",
#     #                     "lane": 3,
#     #                     "cycleCount": 302
#     #                 }
#     #             ]
#     #         },
#     #         {
#     #             "libraryId": "L2500180",
#     #             "bclConvertData": [
#     #                 {
#     #                     "libraryId": "L2500180",
#     #                     "index": "TCTTGTTT+GTGAAAGG",
#     #                     "lane": 2,
#     #                     "cycleCount": 302
#     #                 }
#     #             ]
#     #         }
#     #     ]
#     # }

