#!/usr/bin/env python3

"""
Given a fastq id, collect the fastq list row from the fastq id
"""
from typing import Dict, List, Union
from fastq_tools import get_fastq, FastqListRow


def handler(event, context) -> Dict[str, Union[List[str], FastqListRow]]:
    """
    Given a fastq id, collect the fastq list row from the fastq id
    :param event:
    :param context:
    :return:
    """
    # Get the fastq object
    fastq_obj = get_fastq(event["fastqId"])

    # Get the s3 ingest ids
    ingest_ids = list(filter(
        lambda ingest_id_iter_: ingest_id_iter_ is not None,
        # Get the s3IngestId from the fastq objects
        [
            fastq_obj['readSet']['r1']['ingestId'],
            (
                fastq_obj['readSet']['r2']['ingestId']
                if fastq_obj['readSet']['r2'] else None
            ),
        ]
    ))

    return {
        "fastqObject": fastq_obj,
        "ingestIds": ingest_ids
    }
