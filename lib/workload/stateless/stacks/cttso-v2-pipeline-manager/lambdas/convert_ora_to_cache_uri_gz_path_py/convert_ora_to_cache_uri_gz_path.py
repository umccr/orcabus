#!/usr/bin/env python

"""
Given a fastq list row in ora format, a cache uri and a sample id,

Determine the output gzip path for the fastq files

Returns read_1_gz_output_uri and read_2_gz_output_uri
"""

from urllib.parse import (urlparse, urlunparse)
from pathlib import Path

def extend_url(url, path_ext: str) -> str:
    """
    Extend the url path with the path_ext
    """
    url_obj = urlparse(url)

    return str(
        urlunparse(
            (
                url_obj.scheme,
                url_obj.netloc,
                str(Path(url_obj.path) / path_ext),
                url_obj.params,
                url_obj.query,
                url_obj.fragment
            )
        )
    )


def handler(event, context):
    # Get the input event
    cache_uri = event['cache_uri']

    # Get the input event
    sample_id = event['sample_id']

    # Get the input event
    fastq_list_row = event['fastq_list_row']
    read_1_ora_file_uri = fastq_list_row['read1FileUri']
    read_2_ora_file_uri = fastq_list_row['read2FileUri']

    # Extend the cache uri to include the sample id
    sample_cache_uri = extend_url(cache_uri, sample_id)

    # Get the file name from the ora file uri
    # And replace the .ora extension with .gz
    read_1_file_name = Path(read_1_ora_file_uri).name.replace('.ora', '.gz')
    read_2_file_name = Path(read_2_ora_file_uri).name.replace('.ora', '.gz')

    # Get the output uri for the gz files
    return {
        'read_1_gz_output_uri': extend_url(sample_cache_uri, read_1_file_name),
        'read_2_gz_output_uri': extend_url(sample_cache_uri, read_2_file_name)
    }
