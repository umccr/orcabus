#!/usr/bin/env python

# Imports
import json
import ulid
import re
from fastapi import Request

from .globals import (
    ORCABUS_ULID_REGEX_MATCH,
    GET_LIBRARY_ORCABUS_ID_FROM_LIBRARY_ID_LAMBDA_FUNCTION_NAME,
    GET_LIBRARY_ID_FROM_LIBRARY_ORCABUS_ID_LAMBDA_FUNCTION_NAME,
    GET_PRESIGNED_URL_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_NAME,
    GET_S3_INGEST_ID_FROM_S3_URI_LAMBDA_FUNCTION_NAME,
    GET_S3_URI_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_NAME
)

import boto3
import typing

if typing.TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef


def get_ulid() -> str:
    return ulid.new().str


def is_orcabus_ulid(query: str) -> bool:
    """
    Matches xxx.<ULID> pattern
    :return:
    """
    return ORCABUS_ULID_REGEX_MATCH.match(query) is not None

def to_camel_case(snake_str):
    if isinstance(snake_str, str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    elif isinstance(snake_str, list):
        return [to_camel_case(item) for item in snake_str]
    elif isinstance(snake_str, dict):
        return {to_camel_case(k): to_camel_case(v) for k, v in snake_str.items()}
    else:
        return snake_str


def to_snake_case(camel_str):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()


def convert_keys_to_snake_case(data):
    if isinstance(data, dict):
        return {to_snake_case(k): convert_keys_to_snake_case(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_snake_case(item) for item in data]
    else:
        return data


async def convert_body_to_snake_case(request: Request):
    body = await request.json()
    return convert_keys_to_snake_case(body)


def get_aws_lambda_client() -> 'LambdaClient':
    return boto3.client('lambda')


def run_lambda_function(function_name: str, payload: str) -> str:
    client = get_aws_lambda_client()
    response: InvocationResponseTypeDef = client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=payload
    )
    return response['Payload'].read().decode('utf-8')


def get_library_orcabus_id_from_library_id(library_id: str) -> str:
    library_obj = json.loads(run_lambda_function(GET_LIBRARY_ORCABUS_ID_FROM_LIBRARY_ID_LAMBDA_FUNCTION_NAME, library_id))

    if 'orcabusId' not in library_obj:
        raise Exception(f"Library with id {library_id} not found")

    return library_obj['orcabusId']


def get_library_id_from_library_orcabus_id(library_orcabus_id: str) -> str:
    library_obj = json.loads(run_lambda_function(GET_LIBRARY_ID_FROM_LIBRARY_ORCABUS_ID_LAMBDA_FUNCTION_NAME, library_orcabus_id))

    if 'libraryId' not in library_obj:
        raise Exception(f"Library with id {library_orcabus_id} not found")

    return library_obj['libraryId']


def get_presigned_url_from_s3_ingest_id(s3_ingest_id: str) -> typing.Dict:
    presigned_url_response_body = json.loads(run_lambda_function(GET_PRESIGNED_URL_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_NAME, s3_ingest_id))

    if 'presignedUrl' not in presigned_url_response_body:
        raise Exception(f"Presigned URL not found for S3 URI {s3_ingest_id}")

    return presigned_url_response_body


def get_s3_ingest_id_from_s3_uri(s3_uri: str) -> str:
    s3_ingest_id_response_body = json.loads(run_lambda_function(GET_S3_INGEST_ID_FROM_S3_URI_LAMBDA_FUNCTION_NAME, s3_uri))

    if 's3IngestId' not in s3_ingest_id_response_body:
        raise Exception(f"S3 Ingest ID not found for S3 URI {s3_uri}")

    return s3_ingest_id_response_body


def get_s3_uri_from_s3_ingest_id(s3_ingest_id: str) -> str:
    s3_uri_response_body = json.loads(run_lambda_function(GET_S3_URI_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_NAME, s3_ingest_id))

    if 's3Uri' not in s3_uri_response_body:
        raise Exception(f"S3 Ingest ID not found for S3 URI {s3_ingest_id}")

    return s3_uri_response_body
