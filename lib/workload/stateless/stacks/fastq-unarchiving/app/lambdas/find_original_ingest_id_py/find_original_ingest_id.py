#!/usr/bin/env python3

"""
Find the original ingest id

Given a list of fastq ids and a file name, find the fastq id where their s3 uri for R1 or R2 matches the filename

We need to do this since the s3 steps copy won't necessarily copy over the original ingest id and tags
"""

from typing import List, Dict
from urllib.parse import urlparse
from pathlib import Path

# Local layer imports
from fastq_tools import get_fastq, FastqListRow


def get_fastq_objects(fastq_ids: List[str]) -> List[FastqListRow]:
    return list(map(
        lambda fastq_id: get_fastq(fastq_id, includeS3Detail=True),
        fastq_ids
    ))


def find_original_ingest_id(fastq_ids: List[str], s3_uri: str) -> Dict[str, str]:
    filename = Path(urlparse(s3_uri).path).name
    fastq_objects = get_fastq_objects(fastq_ids)
    for fastq_object in fastq_objects:
        if Path(urlparse(fastq_object['readSet']['r1']['s3Uri']).path).name == filename:
            return {
                "fastqId": fastq_object['id'],
                "ingestId": fastq_object['readSet']['r1']['ingestId']
            }
        if fastq_object['readSet'].get("r2", None) is not None:
            if Path(urlparse(fastq_object['readSet']['r2']['s3Uri']).path).name == filename:
                return {
                    "fastqId": fastq_object['id'],
                    "ingestId": fastq_object['readSet']['r2']['ingestId']
                }
    raise ValueError("Filename not found in fastq ids")


def handler(event, context) -> Dict[str, str]:
    """
    Given a list of fastq ids and a file name, find the fastq id where their s3 uri for R1 or R2 matches the filename
    :param event:
    :param context:
    :return:
    """
    fastq_ids = event.get("fastqIdList", [])
    s3_uri = event.get("s3Uri", "")
    return find_original_ingest_id(fastq_ids, s3_uri)
