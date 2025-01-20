#!/usr/bin/env python3

"""
Get presigend url from the s3 uri fastq manager
"""

from filemanager_tools import get_presigned_url, get_file_object_from_s3_uri


def handler(event, context):
    """
    Get the presigned url from the s3 uri
    :param event:
    :param context:
    :return:
    """

    # Part 1 - Get the s3 uri object
    s3_obj = get_file_object_from_s3_uri(event['s3_uri'])

    # Part 2 - Return the ingest id
    return {
        "s3_ingest_id": s3_obj.ingestId
    }


