#!/usr/bin/env python3

"""
Given a fastq id, collect the fastq object with s3 uris,

Return a dictionary with the following keys:
{
  "fastqId": "fastqId",
  "s3UriList": ["s3Uri1", "s3Uri2", ...],
}
"""

from fastq_tools import get_fastq
from typing import Dict, TypedDict, List, Union

class S3Obj(TypedDict):
    ingestId: str
    s3Uri: str
    sha256: str
    storageClass: str


def handler(event, context) -> Dict[str, Union[str, List[S3Obj]]]:
    """
    Given a fastq id, collect the fastq object with s3 uris,
    :param event:
    :param context:
    :return:
    """
    fastq_id = event['fastqId']

    fastq_obj = get_fastq(fastq_id, includeS3Details=True)

    s3_objs = [
        fastq_obj["readSet"]["r1"],
    ]

    if fastq_obj["readSet"].get("r2", None):
        s3_objs.append(fastq_obj["readSet"]["r2"])

    return {
        "fastqId": fastq_id,
        "fastqObj": fastq_obj,
        "s3Objs": s3_objs,
    }
