#!/usr/bin/env python3

"""
Miscellaneous utilities for parsing through compressed strings
"""

import json
from base64 import b64encode, b64decode
import gzip
from pathlib import Path
from typing import Dict, List, Union


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


def decompress_file(input_file: Path, output_file: Path):
    """
    Given a gzipped compressed file as an input, decompress and write to output file
    Args:
        input_file:
        output_file:

    Returns:

    """
    with gzip.open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            f_out.write(f_in.read())
