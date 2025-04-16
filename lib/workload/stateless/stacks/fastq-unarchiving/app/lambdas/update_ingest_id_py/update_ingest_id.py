#!/usr/bin/env python3

"""
Update the ingest id using the filemanager tools api

Use the filemanager tools layer to update the ingest id for a file.

We have to do this for each file in the ingest.

"""
from typing import Dict, List
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from fastq_tools import get_fastq, FastqListRow
from filemanager_tools import update_ingest_id, get_file_object_from_s3_uri


def handler(event, context) -> Dict[str, bool]:
    """
    Not a trivial task, we first need to match the ingest id to the file id
    and then update the ingest id for the file.
    Therefore we get all fastqIds from the top-level map, and to match to the bucket, key prefix provided in the bottom-level map.
    :param event:
    :param context:
    :return:
    """
    ingest_id = event["ingestId"]
    bucket = event['bucket']
    key = event['key']

    # Get the file id from the file manager
    file_manager_file_object = get_file_object_from_s3_uri(
        str(urlunparse(("s3", bucket, key, None, None, None)))
    )
    file_manager_ingest_id = file_manager_file_object['ingestId']

    # Check if the ingest ids match
    ingest_id_updated_complete = False
    if ingest_id != file_manager_ingest_id:
        ingest_id_updated_complete = True
        update_ingest_id(file_manager_file_object['s3ObjectId'], ingest_id)

    return {
        "ingestIdUpdatedComplete": ingest_id_updated_complete
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "fastqId": "fqr.01JN25WGXBBC8G86B4N23VAQ85",
#                     "ingestId": "019387f3-4cf8-77b1-9469-ecd9c5749dd2",
#                     "bucket": "pipeline-prod-cache-503977275616-ap-southeast-2",
#                     "key": "byob-icav2/production/restored/14d/year=2025/month=04/day=03/b1cba8cf-91a2-4ec9-a7c5-9a270721d013/240105_A00130_0284_AHWLVYDSX7/PRJ231299_L2301517_S2_L001_R2_001.fastq.ora"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "ingestIdUpdatedComplete": true
#     # }
#
