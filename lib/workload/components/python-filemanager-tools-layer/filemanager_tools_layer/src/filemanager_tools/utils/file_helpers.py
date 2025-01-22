#!/usr/bin/env python3

from .models import (FileObject)
from .aws_helpers import get_bucket_key_pair_from_uri
from .request_helpers import get_request_response_results, get_response
from .globals import S3_LIST_ENDPOINT


def get_file_object_from_s3_uri(s3_uri: str) -> FileObject:
    s3_bucket, s3_key = get_bucket_key_pair_from_uri(s3_uri)

    response = get_request_response_results(S3_LIST_ENDPOINT, {
        "bucket": s3_bucket,
        "key": s3_key
    })

    # Assert we got one result
    assert len(response) == 1, f"Expected 1 result, got {len(response)}"

    # Return as a FileObject model
    return FileObject(**response[0])


def get_file_object_from_id(file_object_id: str) -> FileObject:
    """
    Get file object from the id
    :param id: 
    :return: 
    """
    response = get_request_response_results(f"{S3_LIST_ENDPOINT}/{file_object_id}")

    # Assert we got one result
    assert len(response) == 1, f"Expected 1 result, got {len(response)}"

    # Return as a FileObject model
    return FileObject(**response[0])


def get_file_object_from_ingest_id(ingest_id: str) -> FileObject:
    response = get_request_response_results(S3_LIST_ENDPOINT, {
        "ingestId": ingest_id
    })

    # Assert we got one result
    assert len(response) == 1, f"Expected 1 result, got {len(response)}"

    # Return as a FileObject model
    return FileObject(**response[0])


def list_files_from_portal_run_id(portal_run_id: str) -> list:
    response = get_request_response_results(S3_LIST_ENDPOINT, {
        "portalRunId": portal_run_id
    })

    # Return as a list of FileObject models
    return [FileObject(**file) for file in response]


def get_presigned_url(s3_object_id: str) -> str:
    """
    Get presigned url
    :param s3_object_id:
    :return:
    """

    response = get_response(f"{S3_LIST_ENDPOINT}/presign/{s3_object_id}")

    return str(response)
