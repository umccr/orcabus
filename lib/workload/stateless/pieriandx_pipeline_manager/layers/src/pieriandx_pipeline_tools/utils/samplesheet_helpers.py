#!/usr/bin/env python
from typing import Dict

from base64 import b64decode
import gzip

def read_v2_samplesheet(b64gzipped_samplesheet: str) -> Dict:
    """
    Decode and decompress a base64 encoded and gzipped samplesheet file.

    Args:
        b64gzipped_samplesheet:

    Returns:

    """

    from .compression_helpers import decompress_dict

    return decompress_dict(b64gzipped_samplesheet)
