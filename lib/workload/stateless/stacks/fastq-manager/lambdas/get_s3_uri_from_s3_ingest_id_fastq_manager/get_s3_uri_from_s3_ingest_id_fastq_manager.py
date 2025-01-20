#!/usr/bin/env python3

"""
Get presigend url from the s3 uri fastq manager
"""

from filemanager_tools import get_file_object_from_ingest_id
from urllib.parse import urlunparse


def handler(event, context):
    """
    Get the presigned url from the s3 uri
    :param event:
    :param context:
    :return:
    """

    # Part 1 - Get the s3 uri object
    s3_obj = get_file_object_from_ingest_id(event['s3_ingest_id'])

    # Part 2 - Return the ingest id
    return {
        "s3_uri": str(
            urlunparse((
                "s3", s3_obj.bucket, s3_obj.key,
                None, None, None
            ))
        )
    }
