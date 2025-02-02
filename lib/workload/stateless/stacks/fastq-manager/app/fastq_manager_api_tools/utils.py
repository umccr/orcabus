#!/usr/bin/env python

# Imports
import json
from os import environ
import ulid
import boto3
import typing
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from pydantic.alias_generators import (
    to_snake as pydantic_to_snake,
    to_camel as pydantic_camel
)

from .globals import (
    ORCABUS_ULID_REGEX_MATCH,
    GET_LIBRARY_ORCABUS_ID_FROM_LIBRARY_ID_LAMBDA_FUNCTION_ARN_ENV_VAR,
    GET_LIBRARY_ID_FROM_LIBRARY_ORCABUS_ID_LAMBDA_FUNCTION_ARN_ENV_VAR,
    GET_PRESIGNED_URL_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_ARN_ENV_VAR,
    GET_S3_INGEST_ID_FROM_S3_URI_LAMBDA_FUNCTION_ARN_ENV_VAR,
    GET_S3_URI_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_ARN_ENV_VAR, CONTEXT_PREFIX
)

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


async def sanitise_fastq_orcabus_id(fastq_id: str) -> str:
    if ORCABUS_ULID_REGEX_MATCH.match(fastq_id):
        return fastq_id
    elif ORCABUS_ULID_REGEX_MATCH.match(f"{CONTEXT_PREFIX}.{fastq_id}"):
        return f"{CONTEXT_PREFIX}.{fastq_id}"
    raise ValueError(f"Invalid fastq list row id '{fastq_id}'")


async def parse_ntsm(ntsm_uri: str) -> str:
    return ntsm_uri



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
    return json.loads(
        run_lambda_function(
            environ.get(GET_LIBRARY_ORCABUS_ID_FROM_LIBRARY_ID_LAMBDA_FUNCTION_ARN_ENV_VAR),
            json.dumps({"library_id": library_id})
        )
    )['orcabus_id']


def get_library_id_from_library_orcabus_id(library_orcabus_id: str) -> str:
    return json.loads(
        run_lambda_function(
            environ.get(GET_LIBRARY_ID_FROM_LIBRARY_ORCABUS_ID_LAMBDA_FUNCTION_ARN_ENV_VAR),
            json.dumps({"library_orcabus_id": library_orcabus_id})
        )
    )['library_id']


def get_presigned_url_from_s3_ingest_id(s3_ingest_id: str) -> str:
    return json.loads(
        run_lambda_function(
            environ.get(GET_PRESIGNED_URL_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_ARN_ENV_VAR),
            json.dumps({"s3_ingest_id": s3_ingest_id})
        )
    )['presigned_url']


def get_s3_ingest_id_from_s3_uri(s3_uri: str) -> str:
    return json.loads(
        run_lambda_function(
            environ.get(GET_S3_INGEST_ID_FROM_S3_URI_LAMBDA_FUNCTION_ARN_ENV_VAR),
            json.dumps({"s3_uri": s3_uri})
        )
    )['s3_ingest_id']


def get_s3_uri_from_s3_ingest_id(s3_ingest_id: str) -> str:
    return json.loads(
        run_lambda_function(
            environ.get(GET_S3_URI_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_ARN_ENV_VAR),
            json.dumps({"s3_ingest_id": s3_ingest_id})
        )
    )['s3_uri']


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


def datetime_to_isoformat(dt: datetime) -> str:
    return dt.isoformat(sep="T", timespec="seconds").replace("+00:00", "Z")


def to_snake(s: str) -> str:
    return (
        pydantic_to_snake(s)
        .replace("s_3", "s3")
        .replace("md_5sum", "md5sum")
        .replace("rawmd_5_sum", "raw_md5sum")
        .replace("r_1", "r1")  # R1 and R2
        .replace("r_2", "r2")
        .replace("index_2", "index2")
        .replace("q_20", "q20")
    )


def to_camel(s: str) -> str:
    return (
        pydantic_camel(s)
        .replace("Md5Sum", "Md5sum")
        # Sometimes we're to_camel twice and that messes with things
        .replace("rawmd5Sum", "rawMd5sum")
    )