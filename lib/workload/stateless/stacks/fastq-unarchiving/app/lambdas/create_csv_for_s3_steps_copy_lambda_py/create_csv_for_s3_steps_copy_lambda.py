#!/usr/bin/env python3

"""
Create the csv for s3 copy steps,

Each row comprises the s3 bucket, s3 key

Using pandas is overkill but #wheninrome

We take an

"""
from typing import List, Dict, Tuple

from fastq_tools import get_fastq
from urllib.parse import urlparse
import pandas as pd


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

    return s3_obj.netloc, s3_obj.path


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


def handler(event, context) -> Dict[str, str]:
    """
    Generate the csv for s3 copy steps
    :param event:
    :param context:
    :return:
    """
    fastq_ids = event['fastqIdList']

    copy_data_df = create_csv_for_s3_copy_steps(fastq_ids)

    return {
        'csvStepsCopyData': copy_data_df.to_csv(header=False, index=False),
    }
