#!/usr/bin/env python3

"""
Create the csv for s3 copy steps,

Each row comprises the s3 bucket, s3 key

Using pandas is overkill but #wheninrome

We take an

"""

import typing
from typing import List, Tuple

from fastq_tools import get_fastq
from urllib.parse import urlparse
import pandas as pd
import boto3

# Type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_s3_client() -> 'S3Client':
    return boto3.client('s3')


def upload_file_to_s3(bucket: str, key: str, file_contents: str):
    s3_client = get_s3_client()

    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_contents
    )


def get_s3_uris_from_fastq_id(fastq_id: str) -> List[str]:
    fastq_obj = get_fastq(fastq_id, includeS3Details=True)

    return list(filter(
        lambda s3_uri_iter_: s3_uri_iter_ is not None,
        [
            fastq_obj['readSet']['r1']['s3Uri'],
            fastq_obj['readSet'].get('r2', {}).get('s3Uri', None)
        ]
    ))


def split_s3_uri(s3_uri: str) -> Tuple[str, str]:
    s3_obj = urlparse(s3_uri)

    return s3_obj.netloc, s3_obj.path.lstrip("/")


def create_csv_for_s3_copy_steps(fastq_ids: List[str]) -> pd.DataFrame:
    """
    Create the csv for s3 copy steps,

    Each row comprises the s3 bucket, s3 key

    Using pandas is overkill but #wheninrome

    We take an
    :return:
    """
    rows = []

    for fastq_id in fastq_ids:
        # Get the s3 uris for each fastq id
        s3_uris = get_s3_uris_from_fastq_id(fastq_id)

        # For each s3 uri, split the s3 uris into bucket and key
        for s3_uri in s3_uris:
            bucket, key = split_s3_uri(s3_uri)

            rows.append({
                'bucket': bucket,
                'key': key
            })

    return pd.DataFrame(rows)


def handler(event, context):
    """
    Generate the csv for s3 copy steps
    :param event:
    :param context:
    :return:
    """
    fastq_ids = event['fastqIdList']
    steps_copy_bucket = event['s3StepsCopyBucket']
    steps_copy_key = event['s3StepsCopyKey']

    # Generate the csv
    copy_data_df = create_csv_for_s3_copy_steps(fastq_ids)

    # Uploading to s3
    upload_file_to_s3(
        steps_copy_bucket,
        steps_copy_key,
        copy_data_df.to_csv(header=False, index=False)
    )


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "fastqIdList": [
#                         "fqr.01JP12M6BJ041G2VMCKGW4VNNC"
#                     ],
#                     "s3StepsCopyBucket": "stepss3copy-working66f7dd3f-x4jwbnt6qvxc",  # pragma: allowlist secret
#                     "s3StepsCopyKey": "FASTQ_UNARCHIVING/6afc7752-fa6c-4f90-b53c-2c67ae56621c.0.csv"
#                 },
#                 None
#             )
#         )
#     )
#
#     # aws s3 cp s3://stepss3copy-working66f7dd3f-x4jwbnt6qvxc/FASTQ_UNARCHIVING/6afc7752-fa6c-4f90-b53c-2c67ae56621c.0.csv -
#     # pipeline-dev-cache-503977275616-ap-southeast-2,byob-icav2/development/primary/240424_A01052_0193_BH7JMMDRX5/20240910463b8d5d/Samples/Lane_1/LPRJ240775/LPRJ240775_S1_L001_R1_001.fastq.gz
#     # pipeline-dev-cache-503977275616-ap-southeast-2,byob-icav2/development/primary/240424_A01052_0193_BH7JMMDRX5/20240910463b8d5d/Samples/Lane_1/LPRJ240775/LPRJ240775_S1_L001_R2_001.fastq.gz
