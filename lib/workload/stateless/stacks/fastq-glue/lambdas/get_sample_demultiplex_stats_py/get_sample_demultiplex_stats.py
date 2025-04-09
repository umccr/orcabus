#!/usr/bin/env python3

"""
Get samplesheet demux stats

Import the demux stats file, query for the library of interest and return stats in the following format:

{
    "index": "AAAA+GGGG",
    "lane": 1,
    "library": "sample_name",
    "readCount": 111111
}

Demux stats file has the following columns:
Lane,SampleID,Index,# Reads,# Perfect Index Reads,# One Mismatch Index Reads,# Two Mismatch Index Reads,% Reads,% Perfect Index Reads,% One Mismatch Index Reads,% Two Mismatch Index Reads

"""

# Imports
import pandas as pd
from tempfile import NamedTemporaryFile
import typing
import boto3
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple, Dict, List, Union

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


def read_demux_stats_csv(demux_stats_uri: str) -> pd.DataFrame:
    """
    Pandas Dataframe returned has the following columns:
    Lane,SampleID,Index,# Reads,# Perfect Index Reads,# One Mismatch Index Reads,# Two Mismatch Index Reads,% Reads,% Perfect Index Reads,% One Mismatch Index Reads,% Two Mismatch Index Reads
    :param demux_stats_uri:
    :return:
    """
    bucket, key = get_bucket_key_from_s3_uri(demux_stats_uri)

    # Create a temporary file to store the samplesheet
    temp_file = Path(NamedTemporaryFile(delete=False, suffix=".csv").name)

    # Download the samplesheet from S3
    get_s3_object(bucket, key, temp_file)

    # Read the samplesheet
    return pd.read_csv(
        temp_file,
        # Will always have a header
        header=0
    )


def get_rows_demux_stats_df(
        sample_id: str,
        demux_stats_df: pd.DataFrame,
) -> List[Dict[str, Union[str, int]]]:
    """
    Get the file names from the demultiplex dataframe
    :param sample_id:
    :param demux_stats_df:
    :return:
    """
    return (demux_stats_df.query(
        "SampleID == @sample_id",
    ).assign(
        libraryId=lambda row_iter_: row_iter_["SampleID"],
        lane=lambda row_iter_: pd.to_numeric(row_iter_["Lane"]),
        readCount=lambda row_iter_: row_iter_["# Reads"],
    )[[
        "libraryId", "lane", "readCount"
    ]].to_dict(
        orient='records'
    ))


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Get the read counts from the demux stats file
    :param event:
    :param context:
    :return:
    """

    # Get the sample id and samplesheet uri from the event
    sample_id = event['sampleId']
    demux_stats_uri = event['demuxStatsUri']

    # Read the samplesheet
    demux_stats_df = read_demux_stats_csv(demux_stats_uri)

    # Return fastq list rows for this sample
    return {
        'sampleDemuxStats': get_rows_demux_stats_df(
            sample_id,
            demux_stats_df
        )
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
                "demuxStatsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Reports/Demultiplex_Stats.csv"
            },
            None
        ),
        indent=4
    ))

    # {
    #     "sampleDemuxStats": [
    #         {
    #             "libraryId": "L2401544",
    #             "lane": 2,
    #             "readCount": 56913395
    #         },
    #         {
    #             "libraryId": "L2401544",
    #             "lane": 3,
    #             "readCount": 62441372
    #         }
    #     ]
    # }
