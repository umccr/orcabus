#!/usr/bin/env python3

""""
SFN LAMBDA HANDLER: __generate_presigned_url_for_data_objects_lambda_function_arn__

Intro:

Generate a presigned url for a data object using the ICAv2 API

"""

# Imports
from urllib.parse import urlunparse, urlparse, parse_qs
from typing import Dict, List

from filemanager_tools import FileObject

from datetime import datetime, timedelta, timezone

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


def extract_query_params_from_presigned_url(presigned_url: str) -> Dict[str, List[str]]:
    # parse in the url
    parsed_url = urlparse(presigned_url)

    # Extract the query parameters
    return parse_qs(parsed_url.query)


def extract_amz_expires(presigned_url: str) -> timedelta:
    # Retrieve the X-Amz-Expires value
    amz_expires = extract_query_params_from_presigned_url(presigned_url).get('X-Amz-Expires', [None])[0]

    return timedelta(seconds=int(amz_expires))


def extract_amz_date(presigned_url: str) -> datetime:
    # Retrieve the X-Amz-Date value
    amz_date = extract_query_params_from_presigned_url(presigned_url).get('X-Amz-Date', [None])[0]

    return datetime.strptime(amz_date, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def get_presigned_url_expiry_as_isoformat(presigned_url: str) -> str:
    return (extract_amz_date(presigned_url) + extract_amz_expires(presigned_url)).isoformat(
        sep="T", timespec="seconds"
    ).replace("+00:00", "Z")


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Get the presigned url for data objects
    :param event:
    :param context:
    :return:
    """

    # Get the input
    ingest_id_list: List[str] = event.get("ingestIdList", None)

    # Check if s3_uri is None
    if ingest_id_list is None:
        raise ValueError("ingestIdList input parameter is required")

    return {
        "ingestIdsWithPresignedUrlDataOutputs": list(map(
            lambda presigned_url_dict_iter: {
                "ingestId": presigned_url_dict_iter['ingestId'],
                "presignedUrl": presigned_url_dict_iter['presignedUrl'],
                "presignedExpiry": get_presigned_url_expiry_as_isoformat(presigned_url_dict_iter['presignedUrl'])
            },
            get_presigned_urls_from_ingest_ids(ingest_id_list)
        ))
    }


if __name__ == "__main__":
    from os import environ
    import json
    environ['AWS_REGION'] = 'ap-southeast-2'
    environ['AWS_PROFILE'] = 'umccr-production'
    environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
    environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
    print(json.dumps(
        handler(
            {
                "ingestIdList": [
                    "01960822-f3ee-77d0-8fa4-91d5c2e17ad9",
                ]
            },
            None
        ),
        indent=4)
    )

      # {
      #     "ingestId": "01960822-f3ee-77d0-8fa4-91d5c2e17ad9",
      #     "presignedUrl": "...",
      #     "presignedExpiry": "2025-04-14T22:52:35Z"
      # },
