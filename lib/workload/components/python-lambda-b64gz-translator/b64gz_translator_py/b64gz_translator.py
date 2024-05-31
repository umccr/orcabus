#!/usr/bin/env python

"""
Convert b64gzip to dict or vice versa
"""

from base64 import b64decode, b64encode
from typing import Union, Dict, List
import gzip
import json


def compress_dict(input_dict: Union[Dict, List]) -> str:
    """
    Given a json input, compress to a base64 encoded string

    param: input_dict: input dictionary to compress

    Returns: gzipped compressed base64 encoded string
    """

    # Compress
    return b64encode(
        gzip.compress(
            json.dumps(input_dict).encode('utf-8')
        )
    ).decode("utf-8")


def decompress_dict(input_compressed_b64gz_str: str) -> Union[Dict, List]:
    """
    Given a base64 encoded string, decompress and return the original dictionary
    Args:
        input_compressed_b64gz_str:

    Returns: decompressed dictionary or list
    """

    # Decompress
    return json.loads(
        gzip.decompress(
            b64decode(input_compressed_b64gz_str.encode('utf-8'))
        )
    )


def handler(event, context):
    if event.get('decompress', False):
        return {
            "decompressed_dict": decompress_dict(event['input'])
        }
    return {
        "compressed_b64gz_str": compress_dict(event['input'])
    }
