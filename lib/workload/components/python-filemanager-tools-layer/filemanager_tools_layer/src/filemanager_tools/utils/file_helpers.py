#!/usr/bin/env python3
from functools import reduce
from operator import concat
from typing import List, Dict

from .errors import S3FileNotFoundError, S3DuplicateFileCopyError
from .models import FileObject
from .aws_helpers import get_bucket_key_pair_from_uri
from .request_helpers import get_request_response_results, get_response
from .globals import S3_LIST_ENDPOINT
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from itertools import batched


def get_file_object_from_s3_uri(s3_uri: str) -> FileObject:
    s3_bucket, s3_key = get_bucket_key_pair_from_uri(s3_uri)

    response = get_request_response_results(S3_LIST_ENDPOINT, {
        "bucket": s3_bucket,
        "key": s3_key,
        "currentState": 'true'
    })

    if len(response) == 0:
        # Try again with current_state=False
        response = get_request_response_results(S3_LIST_ENDPOINT, {
            "bucket": s3_bucket,
            "key": s3_key,
            "currentState": 'false'
        })

    if len(response) == 0:
        raise S3FileNotFoundError(s3_uri=s3_uri)

    # Filter responses with no "s3IngestId" field
    response = list(filter(
        lambda result_iter_: result_iter_.get("ingestId", None) is not None,
        response
    ))

    if not len(response) ==  1:
        raise S3DuplicateFileCopyError(s3_uri=s3_uri)

    # Return as a FileObject model
    return FileObject(**response[0])


def get_file_object_from_id(s3_object_id: str) -> FileObject:
    """
    Get file object from the id
    :param s3_object_id:
    :return: 
    """
    response = get_request_response_results(f"{S3_LIST_ENDPOINT}/{s3_object_id}")

    if len(response) == 0:
        raise S3FileNotFoundError(s3_object_id=s3_object_id)
    elif not len(response) == 1:
        raise S3DuplicateFileCopyError(s3_object_id=s3_object_id)

    # Return as a FileObject model
    return FileObject(**response[0])


def get_file_object_from_ingest_id(ingest_id: str) -> FileObject:
    response = get_request_response_results(S3_LIST_ENDPOINT, {
        "ingestId": ingest_id
    })

    if len(response) == 0:
        raise S3FileNotFoundError(ingest_id=ingest_id)
    elif not len(response) == 1:
        raise S3DuplicateFileCopyError(ingest_id=ingest_id)

    # Return as a FileObject model
    return FileObject(**response[0])


def list_files_from_portal_run_id(portal_run_id: str) -> List[FileObject]:
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


def get_s3_object_id_from_s3_uri(s3_uri: str) -> str:
    return get_file_object_from_s3_uri(s3_uri)['s3ObjectId']


def get_s3_uri_from_s3_object_id(s3_object_id: str) -> str:
    file_object: FileObject = get_file_object_from_id(s3_object_id)
    return f"s3://{file_object['bucket']}/{file_object['key']}"


def get_s3_uri_from_ingest_id(ingest_id: str) -> str:
    file_object: FileObject = get_file_object_from_ingest_id(ingest_id)
    return f"s3://{file_object['bucket']}/{file_object['key']}"


def get_ingest_id_from_s3_uri(s3_uri: str) -> str:
    return get_file_object_from_s3_uri(s3_uri)['ingestId']


def get_presigned_url_from_ingest_id(ingest_id: str) -> str:
    """
    Get presigned url from ingest id
    :param ingest_id:
    :return:
    """
    return get_presigned_url(get_file_object_from_ingest_id(ingest_id)['s3ObjectId'])


def get_presigned_url_expiry(s3_presigned_url: str) -> datetime:
    """
    Given a presigned url, return the expiry
    :param s3_presigned_url:
    :return:
    """
    urlobj = urlparse(s3_presigned_url)

    query_dict = dict(map(
        lambda params_iter_: params_iter_.split("=", 1),
        urlparse(s3_presigned_url).query.split("&"))
    )

    # Take the X-Amz-Date value (in 20250121T013812Z format) and add in the X-Amz-Expires value
    creation_time = datetime.strptime(query_dict['X-Amz-Date'], "%Y%m%dT%H%M%SZ")
    expiry_ext = timedelta(seconds=int(query_dict['X-Amz-Expires']))

    return (creation_time + expiry_ext).astimezone(tz=timezone.utc)


def get_s3_uris_from_ingest_ids_map(ingest_ids: List[str]) -> List[Dict[str, str]]:
    # Split by groups of 100
    ingest_id_batches = batched(ingest_ids, 100)

    return list(map(
        lambda s3_obj_iter: {
            "ingestId": s3_obj_iter['ingestId'],
            "uri": f"s3://{s3_obj_iter['bucket']}/{s3_obj_iter['key']}"
        },
        list(reduce(
            concat,
            list(map(
                lambda ingest_id_batch_:
                    get_request_response_results(S3_LIST_ENDPOINT, {
                        "ingestId[]": list(ingest_id_batch_)
                    }),
                ingest_id_batches
            ))
        ))
    ))