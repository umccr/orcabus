#!/usr/bin/env python3

"""
Get samples from the samplesheet

To prevent overloading the step functions, we simply collect all samples from the samplesheet
and return them as a list.

Then in the step function, we can iterate over this list, recollecting the sample, bclconvert data, demux stats
and then creating a fastq set object for each sample.

We get the following as inputs:




"""

# Imports
from tempfile import NamedTemporaryFile
import typing
import boto3
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple, Dict, List
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
    samplesheet_uri = event['sampleSheetUri']

    # Read the samplesheet
    samplesheet = read_v2_samplesheet(samplesheet_uri)

    # Return the bclconvert data
    return {
        'samplesList': list(set(list(map(
            lambda bclconvert_data_row_: bclconvert_data_row_['sample_id'],
            samplesheet['bclconvert_data']
        ))))
    }

