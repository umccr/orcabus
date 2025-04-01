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
from tempfile import NamedTemporaryFile
import typing
import boto3
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple, Dict, List, Optional, Union
import re
from v2_samplesheet_maker.functions.v2_samplesheet_reader import v2_samplesheet_reader


# Type hints
if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


# Quick funcs
def get_s3_client() -> 'S3Client':
    return boto3.client('s3')


def get_bucket_key_from_s3_uri(url: str) -> Tuple[str, str]:
    url_obj = urlparse(url)
    return url_obj.netloc, url_obj.path.lstrip("/")


def get_s3_object(bucket: str, key: str, output_path: Path):
    # Make sure parent dir exists
    output_path.parent.mkdir(exist_ok=True, parents=True)

    get_s3_client().download_file(
        Bucket=bucket,
        Key=key,
        Filename=str(output_path)
    )


def read_v2_samplesheet(samplesheet_uri: str) -> Dict:
    bucket, key = get_bucket_key_from_s3_uri(samplesheet_uri)

    # Create a temporary file to store the samplesheet
    temp_file = Path(NamedTemporaryFile(delete=False, suffix=".csv").name)

    # Download the samplesheet from S3
    get_s3_object(bucket, key, temp_file)

    # Read the samplesheet
    return v2_samplesheet_reader(temp_file)


def get_cycle_count_from_bclconvert_data_row(bclconvert_data_row: Dict[str, str]) -> Optional[int]:
    if "override_cycles" in bclconvert_data_row:
        override_cycles = bclconvert_data_row['override_cycles']
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
                "libraryId": bclconvert_row_iter_['sample_id'],
                "index": bclconvert_row_iter_['index'] + ("+" + bclconvert_row_iter_['index2'] if bclconvert_row_iter_['index2'] else ""),
                "lane": int(bclconvert_row_iter_['lane']),
                "cycleCount": (
                    get_cycle_count_from_bclconvert_data_row(bclconvert_row_iter_)
                    if get_cycle_count_from_bclconvert_data_row(bclconvert_row_iter_) is not None
                    else global_cycle_count
                )
            },
            list(filter(
                lambda bclconvert_row_iter_: bclconvert_row_iter_['sample_id'] == sample_id,
                samplesheet['bclconvert_data']
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
    if samplesheet['bclconvert_settings'].get("override_cycles") is not None:
        override_cycles = samplesheet['bclconvert_settings']['override_cycles']
        return get_cycle_count_from_override_cycles(override_cycles)
    return samplesheet['reads']['read_1_cycles'] + samplesheet['reads'].get('read_2_cycles', None)


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Given a samplesheet uri and a sample id,
    Download the samplesheet, get the bclconvert data section
    and return only the rows where sample_id is equal to sampleId
    :param event:
    :param context:
    :return:
    """

    # Get the sample id and samplesheet uri from the event
    sample_id = event['sampleId']
    samplesheet_uri = event['sampleSheetUri']

    # Read the samplesheet
    samplesheet = read_v2_samplesheet(samplesheet_uri)

    # Get override cycles from the samplesheet settings section
    global_cycle_count = get_global_cycle_count(samplesheet)

    # Get the bclconvert data from the samplesheet
    sample_bclconvert_data = get_sample_bclconvert_data_from_v2_samplesheet(
        samplesheet=samplesheet,
        sample_id=sample_id,
        global_cycle_count=global_cycle_count
    )

    # Return the bclconvert data
    return {
        'sampleBclConvertData': sample_bclconvert_data
    }


if __name__ == "__main__":
    import json
    from os import environ
    environ['AWS_PROFILE'] = 'umccr-development'
    environ['AWS_REGION'] = 'ap-southeast-2'
    print(json.dumps(
        handler(
            {
                "sampleId": "L2401544",
                "sampleSheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Reports/SampleSheet.csv"
            },
            None
        ),
        indent=4
    ))

    # {
    #     "sampleBclConvertData": [
    #         {
    #             "libraryId": "L2401544",
    #             "index": "CAAGCTAG+CGCTATGT",
    #             "lane": 2,
    #             "cycleCount": 302
    #         },
    #         {
    #             "libraryId": "L2401544",
    #             "index": "CAAGCTAG+CGCTATGT",
    #             "lane": 3,
    #             "cycleCount": 302
    #         }
    #     ]
    # }

