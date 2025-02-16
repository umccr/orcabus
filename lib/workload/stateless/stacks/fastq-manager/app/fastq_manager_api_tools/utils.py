#!/usr/bin/env python

# Imports
import ulid
import boto3
import typing
from datetime import datetime
from pydantic.alias_generators import (
    to_snake as pydantic_to_snake,
    to_camel as pydantic_camel
)

from .globals import (
    ORCABUS_ULID_REGEX_MATCH,
    CONTEXT_PREFIX
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