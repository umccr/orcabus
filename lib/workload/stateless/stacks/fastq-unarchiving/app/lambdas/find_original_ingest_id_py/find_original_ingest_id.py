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
        lambda fastq_id: get_fastq(fastq_id, includeS3Details=True),
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


# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(json.dumps(
#         handler(
#             {
#                 "fastqIdList": [
#                     "fqr.01JN26CMFST6TTQ955RJETM975",
#                     "fqr.01JN26CMJ114B4GAY0G5E8ARW0"
#                 ],
#                 "s3Uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/restored/14d/year=2025/month=04/day=03/2e505203-396e-46cd-97fb-feea68ac074c/240906_A01052_0225_AHV7FJDSXC/PRJ241412_L2401244_S1_L002_R2_001.fastq.ora"
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "fastqId": "fqr.01JN26CMFST6TTQ955RJETM975",
#     #     "ingestId": "0193909b-d346-7f72-9aff-004165be2725"
#     # }
#

