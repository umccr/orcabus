#!/usr/bin/env python3

"""
SFN PLACEHOLDER: __generate_presigned_url_for_sharing_objects_lambda_function_arn__

Get presigned url for sharing objects

This lambda has permissions to generate a presigned url for sharing objects in this bucket.

This lambda is used for generating the presigned url for the limsrow csv and for the data download file shell script
"""
# Type hints
import typing
from typing import Dict

from s3_json_tools import generate_presigned_url

SEVEN_DAY_EXPIRATION = 604800  # 60 * 60 * 24 * 7

def handler(event, context) -> Dict:
    """
    Generate a presigned url from the bucket name and object key in the event
    :param event:
    :param context:
    :return:
    """

    bucket = event.get('bucket')
    key = event.get('key')

    # Generate a presigned URL for the S3 object
    return {
        "presignedUrl": generate_presigned_url(
            bucket=bucket,
            key=key,
            expiration=SEVEN_DAY_EXPIRATION
        )
    }
