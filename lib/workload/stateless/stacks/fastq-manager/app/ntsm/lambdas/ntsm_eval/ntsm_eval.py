#!/usr/bin/env python3

"""
Evaluate the ntsm for two files
"""
from io import StringIO
from pathlib import Path
from subprocess import run
import typing
import boto3
from urllib.parse import urlparse
from typing import Tuple
from tempfile import NamedTemporaryFile

import pandas as pd

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_s3_client() -> 'S3Client':
    """
    Get the s3 client
    :return:
    """
    return boto3.client('s3')


def get_bucket_key_from_uri(s3_uri: str) -> Tuple[str, str]:
    s3_obj = urlparse(s3_uri)

    return s3_obj.netloc, s3_obj.path.lstrip("/")


def download_s3_file_to_tmp(s3_client: 'S3Client', s3_uri: str) -> Path:
    """
    Download a file from s3 to a temporary file
    :param s3_client:
    :param s3_uri:
    :param tmp_file_path:
    :return:
    """
    bucket, key = get_bucket_key_from_uri(s3_uri)

    with NamedTemporaryFile(delete=False) as tmp_file:
        s3_client.download_fileobj(bucket, key, tmp_file)
        tmp_file_path = Path(tmp_file.name)

    return tmp_file_path


def handler(event, context):
    """
    Collect the two ntsm files
    :param event:
    :param context:
    :return:
    """
    s3 = get_s3_client()
    s3_uri_a = event['ntsmS3UriA']
    s3_uri_b = event['ntsmS3UriB']

    # Download the files
    ntsm_file_a = download_s3_file_to_tmp(s3, s3_uri_a)
    ntsm_file_b = download_s3_file_to_tmp(s3, s3_uri_b)

    # Evaluate the files
    eval_proc = run(
        ['ntsmEval', "--all", ntsm_file_a, ntsm_file_b],
        capture_output=True
    )

    relatedness_df = pd.read_csv(StringIO(eval_proc.stdout.decode('utf-8')), sep="\t")

    # If the coverage is less than 1, we cannot determine the relatedness
    if relatedness_df['cov1'].item() + relatedness_df['cov2'].item() < 1.5:
        return {
            "undetermined": True,
            "relatedness": None,
            "score": relatedness_df["score"].item(),
            "sameSample": None
        }

    if relatedness_df["same"].item() == 1:
        return {
            "undetermined": False,
            "relatedness": relatedness_df["relate"].item(),
            "score": relatedness_df["score"].item(),
            "sameSample": True
        }
    else:
        return {
            "undetermined": False,
            "relatedness": relatedness_df["relate"].item(),
            "score": relatedness_df["score"].item(),
            "sameSample": False
        }


# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     # Setup
#     environ['AWS_PROFILE'] = 'umccr-development'
#
#     # Show output
#     print(json.dumps(
#         handler(
#             {
#                 "ntsmS3UriA": "s3://ntsm-fingerprints-843407916570-ap-southeast-2/ntsm/year=2025/month=03/day=12/fqr.01JP12M6BJ041G2VMCKGW4VNNC.ntsm",
#                 "ntsmS3UriB": "s3://ntsm-fingerprints-843407916570-ap-southeast-2/ntsm/year=2025/month=03/day=15/fqr.01JP12M6F1B3V6PSG1HRWAK89F.ntsm"
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "undetermined": true,
#     #     "relatedness": null,
#     #     "same": null
#     # }



# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     # Setup
#     environ['AWS_PROFILE'] = 'umccr-development'
#
#     # Show output
#     print(json.dumps(
#         handler(
#             {
#                 "ntsmS3UriA": "s3://ntsm-fingerprints-843407916570-ap-southeast-2/ntsm/year=2025/month=03/day=24/eae430c7-b6a2-4f0c-b97e-a3b2dc6f7bad/fqr.01JQ3BEM14JA78EQBGBMB9MHE4.ntsm",
#                 "ntsmS3UriB": "s3://ntsm-fingerprints-843407916570-ap-southeast-2/ntsm/year=2025/month=03/day=24/e04fe96e-3086-4b9e-acc8-7577731b40c5/fqr.01JQ3BEM3A51MEMNS93BBMX19K.ntsm"
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "undetermined": false,
#     #     "relatedness": 0.194714,
#     #     "sameSample": true
#     # }