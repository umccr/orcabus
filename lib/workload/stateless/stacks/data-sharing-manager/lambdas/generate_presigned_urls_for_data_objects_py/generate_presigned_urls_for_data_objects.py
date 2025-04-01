#!/usr/bin/env python3

""""
SFN LAMBDA HANDLER: __generate_presigned_url_for_data_objects_lambda_function_arn__

Intro:

Generate a presigned url for a data object using the ICAv2 API

"""

# Imports
from urllib.parse import urlunparse, urlparse, parse_qs
from typing import Dict, List
import typing

from filemanager_tools import FileObject, get_presigned_url

from datetime import datetime


# Set logging
import logging

from filemanager_tools.utils.file_helpers import get_presigned_urls_from_ingest_ids

logger = logging.getLogger()
logger.setLevel("INFO")

# Set loggers
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_s3_uri_from_s3_file_object(s3_file_object: 'FileObject') -> str:
    return str(urlunparse(
        (
            "s3",
            s3_file_object['bucket'],
            s3_file_object['key'],
            None, None, None
        )
    ))


def extract_amz_expires(presigned_url: str) -> int:
    # Parse the URL
    parsed_url = urlparse(presigned_url)

    # Extract the query parameters
    query_params = parse_qs(parsed_url.query)

    # Retrieve the X-Amz-Expires value
    amz_expires = query_params.get('X-Amz-Expires', [None])[0]

    return int(amz_expires)


def get_presigned_url_expiry_as_isoformat(presigned_url: str) -> str:
    return datetime.fromtimestamp(
        extract_amz_expires(presigned_url)
    ).isoformat(sep="T", timespec="seconds").replace("+00:00", "Z")


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Get the presigned url for data objects
    :param event:
    :param context:
    :return:
    """

    # Get the input
    s3_ingest_id_list: List[str] = event.get("s3IngestIdList", None)

    # Check if s3_uri is None
    if s3_ingest_id_list is None:
        raise ValueError("s3IngestIdList input parameter is required")

    return {
        "s3IngestIdsWithPresignedUrlDataOutputs": list(map(
            lambda presigned_url_dict_iter: {
                "ingestId": presigned_url_dict_iter['ingestId'],
                "presignedUrl": presigned_url_dict_iter['presignedUrl'],
                "presignedExpiry": get_presigned_url_expiry_as_isoformat(presigned_url_dict_iter['presignedUrl'])
            },
            get_presigned_urls_from_ingest_ids(s3_ingest_id_list)
        ))
    }

