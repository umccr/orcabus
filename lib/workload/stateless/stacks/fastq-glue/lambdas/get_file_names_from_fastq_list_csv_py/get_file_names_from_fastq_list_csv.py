#!/usr/bin/env python3

"""
Get file names from the fastq list csv file

Given the inputs sampleId and fastqListUri
find rows where the RGSM of the csv matches the sample id
and return as a list of dicts
"""

# Imports
import pandas as pd
from tempfile import NamedTemporaryFile
import typing
import boto3
from pathlib import Path
from urllib.parse import urlparse, urlunparse
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


def read_fastq_list_csv(fastq_list_csv_uri: str) -> pd.DataFrame:
    """
    Pandas Dataframe returned has the following columns:
    RGID,RGSM,RGLB,Lane,Read1File,Read2File
    :param fastq_list_csv_uri:
    :return:
    """
    bucket, key = get_bucket_key_from_s3_uri(fastq_list_csv_uri)

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


def convert_df_iterable_to_uri(
        bucket: str,
        prefix: str,
        pd_df_iter: pd.DataFrame,
        read_file_column: str
):
    """
    Pandas assign method has a lot to be desired
    :param pd_df_iter:
    :return:
    """
    return pd_df_iter.apply(
        lambda row_iter_: str(
            urlunparse((
                "s3",
                bucket,
                str(
                    Path(prefix) /
                    f"Lane_{row_iter_["Lane"]}" /
                    row_iter_["RGSM"] /
                    row_iter_[read_file_column]
                ),
                None, None, None
            ))
        ),
        axis='columns'
    )


def get_rows_fastq_list_df(
        sample_id_list: List[str],
        fastq_list_df: pd.DataFrame,
        fastq_list_uri: str
) -> List[Dict[str, Union[str, int]]]:
    """
    Get the file names from the fastq list dataframe
    :param sample_id_list:
    :param fastq_list_df:
    :return:
    """
    samples_uri = fastq_list_uri.replace("Reports/fastq_list.csv", "Samples/")
    bucket, key = get_bucket_key_from_s3_uri(samples_uri)
    return fastq_list_df.query(
        "RGSM in @sample_id_list",
    ).assign(
        sampleId=lambda row_iter_: row_iter_["RGSM"],
        lane=lambda row_iter_: pd.to_numeric(row_iter_["Lane"]),
        read1FileUri=lambda row_iter_: convert_df_iterable_to_uri(bucket, key, row_iter_, "Read1File"),
        read2FileUri=lambda row_iter_: (
            convert_df_iterable_to_uri(bucket, key, row_iter_, "Read2File")
            if all(row_iter_["Read2File"])
            else None
        ),
    )[[
        "sampleId",
        "lane",
        "read1FileUri",
        "read2FileUri"
    ]].dropna(
        axis="columns",
    ).to_dict(
        orient='records'
    )


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Get file names from the fastq list csv file

    Given the inputs sampleId and fastqListUri
    find rows where the RGSM of the csv matches the sample id
    and return as a list of dicts
    :param event:
    :param context:
    :return:
    """

    # Get the sample id and samplesheet uri from the event
    sample_id_list = event['sampleIdList']
    fastq_list_uri = event['fastqListUri']

    # Read the samplesheet
    fastq_list_df = read_fastq_list_csv(fastq_list_uri)

    file_names_list = get_rows_fastq_list_df(
        sample_id_list=sample_id_list,
        fastq_list_df=fastq_list_df,
        fastq_list_uri=fastq_list_uri
    )

    # Return fastq list rows for this sample
    return {
        'fileNamesListBySample': list(map(
            lambda sample_id_iter_: {
                "sampleId": sample_id_iter_,
                "fileNamesList": list(filter(
                    lambda file_iter_: file_iter_["sampleId"] == sample_id_iter_,
                    file_names_list
                ))
            },
            sample_id_list
        ))
    }

if __name__ == "__main__":
    import json
    from os import environ
    environ['AWS_PROFILE'] = 'umccr-development'
    environ['AWS_REGION'] = 'ap-southeast-2'
    print(json.dumps(
        handler(
            {
                "sampleIdList": ["L2401544"],
                "fastqListUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Reports/fastq_list.csv"
            },
            None
        ),
        indent=4
    ))

    # {
    #     "fileNamesListBySample": [
    #         {
    #             "sampleId": "L2401544",
    #             "fileNamesList": [
    #                 {
    #                     "sampleId": "L2401544",
    #                     "lane": 2,
    #                     "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
    #                     "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora"
    #                 },
    #                 {
    #                     "sampleId": "L2401544",
    #                     "lane": 3,
    #                     "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
    #                     "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora"
    #                 }
    #             ]
    #         }
    #     ]
    # }