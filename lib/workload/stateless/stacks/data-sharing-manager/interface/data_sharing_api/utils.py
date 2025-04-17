#!/usr/bin/env python

# Imports
import json
import re
from os import environ
from urllib.parse import urlunparse

import ulid
import boto3
import typing
from datetime import datetime

from pydantic.alias_generators import (
    to_snake as pydantic_to_snake,
    to_camel as pydantic_to_camel
)

from .globals import (
    ORCABUS_ULID_REGEX_MATCH, PACKAGE_CONTEXT_PREFIX, PUSH_JOB_CONTEXT_PREFIX
)
from .models import JobStatus


if typing.TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef
    from mypy_boto3_stepfunctions import SFNClient
    from mypy_boto3_stepfunctions.type_defs import StartSyncExecutionOutputTypeDef


def get_ulid() -> str:
    return ulid.new().str


def is_orcabus_ulid(query: str) -> bool:
    """
    Matches xxx.<ULID> pattern
    :return:
    """
    return ORCABUS_ULID_REGEX_MATCH.match(query) is not None


async def sanitise_pkg_orcabus_id(package_id: str) -> str:
    if ORCABUS_ULID_REGEX_MATCH.match(package_id):
        return package_id
    elif ORCABUS_ULID_REGEX_MATCH.match(f"{PACKAGE_CONTEXT_PREFIX}.{package_id}"):
        return f"{PACKAGE_CONTEXT_PREFIX}.{package_id}"
    raise ValueError(f"Invalid package id '{package_id}'")


async def sanitise_psh_orcabus_id(push_job_id: str) -> str:
    if ORCABUS_ULID_REGEX_MATCH.match(push_job_id):
        return push_job_id
    elif ORCABUS_ULID_REGEX_MATCH.match(f"{PUSH_JOB_CONTEXT_PREFIX}.{push_job_id}"):
        return f"{PACKAGE_CONTEXT_PREFIX}.{push_job_id}"
    raise ValueError(f"Invalid package id '{push_job_id}'")


async def sanitise_status(status: JobStatus) -> str:
    return status


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


def datetime_to_isodate(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def datetime_to_hf_format(dt: datetime) -> str:
    return f"{str(int(dt.strftime("%d")))} {dt.strftime("%b")}, {dt.strftime("%Y")}"


def datetime_to_isoformat(dt: datetime) -> str:
    return dt.isoformat(sep="T", timespec="seconds").replace("+00:00", "Z")


def to_snake(s: str) -> str:
    # Pydantic adds an underscore between a lowercase letter and a digit
    # We want to remove this underscore
    return re.sub(r'([a-z])_([0-9])', lambda m: f'{m.group(1)}{m.group(2)}', pydantic_to_snake(s))


def to_camel(s: str) -> str:
    # Pydantic to_camel is not reproducible
    # 'raw_md5sum' -> to_camel -> 'rawMd5Sum' -> to_camel -> 'rawmd5Sum'
    # But we also have trouble with
    # r1_gzip -> to_camel -> 'r1Gzip' (as it should be)
    # So we convert to snake case first
    s = to_snake(s)
    # And extend any 'digit' + underscore + letter to 'digit' + double under score + letter
    s = re.sub(r'([0-9])_([a-z])', lambda m: f'{m.group(1)}__{m.group(2)}', s)
    # Then we convert to camel
    s = pydantic_to_camel(s)
    # Pydantic adds a capital letter after a digit
    # We want to remove this capital letter
    s = re.sub(r'([0-9])([A-Z])', lambda m: f'{m.group(1)}{m.group(2).lower()}', s)
    # We then want to remove the double underscore
    s = re.sub(r'([0-9])__([A-Z])', lambda m: f'{m.group(1)}{m.group(2)}', s)
    return s



# AWS Things
def get_sfn_client() -> 'SFNClient':
    return boto3.client('stepfunctions')


def get_ssm_client() -> 'SSMClient':
    return boto3.client('ssm')


def get_packaging_endpoint_url() -> str:
    return environ.get("DATA_SHARING_BASE_URL") + "api/v1/package/"


def get_push_endpoint_url() -> str:
    return environ.get("DATA_SHARING_BASE_URL") + "api/v1/push/"


# Launch sfn
def launch_sfn(sfn_name: str, sfn_input: dict) -> str:
    sfn_client = get_sfn_client()
    response = sfn_client.start_execution(
        stateMachineArn=sfn_name,
        input=json.dumps(sfn_input)
    )
    return response['executionArn']


def launch_sync_sfn(sfn_name: str, sfn_input: dict) -> 'StartSyncExecutionOutputTypeDef':
    sfn_client = get_sfn_client()
    response = sfn_client.start_sync_execution(
        stateMachineArn=sfn_name,
        input=json.dumps(sfn_input)
    )
    return response


# Abort sfn
def abort_sfn(execution_arn: str) -> None:
    sfn_client = get_sfn_client()
    sfn_client.stop_execution(
        executionArn=execution_arn
    )
    return None


def get_s3_packaging_prefix(package_id: str) -> str:
    current_time = datetime.now()
    return f"packages/year={current_time.year}/month={str(current_time.month).zfill(2)}/day={str(current_time.day).zfill(2)}/{package_id}/"


def get_push_logs_uri(push_job_id: str) -> str:
    current_time = datetime.now()
    return str(urlunparse((
        "s3",
        environ.get("PACKAGE_BUCKET_NAME"),
        f"push-logs/year={current_time.year}/month={str(current_time.month).zfill(2)}/day={str(current_time.day).zfill(2)}/{push_job_id}.parquet",
        None, None, None
    )))
