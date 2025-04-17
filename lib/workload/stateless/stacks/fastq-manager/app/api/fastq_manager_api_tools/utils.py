#!/usr/bin/env python
import re
from functools import reduce
from operator import concat
from os import environ
# Imports
from typing import Optional, List
import ulid
import boto3
import typing
from datetime import datetime
from pydantic.alias_generators import (
    to_snake as pydantic_to_snake,
    to_camel as pydantic_to_camel
)

from metadata_tools import get_sample_orcabus_id_from_sample_id, list_libraries_in_sample, \
    get_subject_orcabus_id_from_subject_id, list_libraries_in_subject, get_individual_orcabus_id_from_individual_id, \
    list_libraries_in_individual, get_project_orcabus_id_from_project_id, list_libraries_in_project
from .globals import (
    ORCABUS_ULID_REGEX_MATCH,
    FQLR_CONTEXT_PREFIX, FQS_CONTEXT_PREFIX
)

if typing.TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef
    from mypy_boto3_stepfunctions import SFNClient


def get_ulid() -> str:
    return ulid.new().str


def is_orcabus_ulid(query: str) -> bool:
    """
    Matches xxx.<ULID> pattern
    :return:
    """
    return ORCABUS_ULID_REGEX_MATCH.match(query) is not None


async def sanitise_fqr_orcabus_id(fastq_id: str) -> str:
    if ORCABUS_ULID_REGEX_MATCH.match(fastq_id):
        return fastq_id
    elif ORCABUS_ULID_REGEX_MATCH.match(f"{FQLR_CONTEXT_PREFIX}.{fastq_id}"):
        return f"{FQLR_CONTEXT_PREFIX}.{fastq_id}"
    raise ValueError(f"Invalid fastq list row id '{fastq_id}'")


def sanitise_fqs_orcabus_id_sync(fastq_set_id: str) -> str:
    if ORCABUS_ULID_REGEX_MATCH.match(fastq_set_id):
        return fastq_set_id
    elif ORCABUS_ULID_REGEX_MATCH.match(f"{FQS_CONTEXT_PREFIX}.{fastq_set_id}"):
        return f"{FQS_CONTEXT_PREFIX}.{fastq_set_id}"
    raise ValueError(f"Invalid fastq set id '{fastq_set_id}'")


async def sanitise_fqs_orcabus_id(fastq_set_id: str) -> str:
    return sanitise_fqs_orcabus_id_sync(fastq_set_id)


async def sanitise_fqs_orcabus_id_x(fastq_set_id_x: str) -> str:
    return sanitise_fqs_orcabus_id_sync(fastq_set_id_x)


async def sanitise_fqs_orcabus_id_y(fastq_set_id_y: str) -> str:
    return sanitise_fqs_orcabus_id_sync(fastq_set_id_y)


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


def get_libraries_from_metadata_query(
    library: str = None,
    library_list: Optional[str] = None,
    sample: str = None,
    sample_list: Optional[str] = None,
    subject: str = None,
    subject_list: Optional[str] = None,
    individual: str = None,
    individual_list: Optional[str] = None,
    project: str = None,
    project_list: Optional[str] = None,
) -> List[str]:
    if library is not None:
        library_list = [library]
    if library_list is not None:
        library_list = list(map(
            lambda library_id_iter_: (
                library_id_iter_ if is_orcabus_ulid(library_id_iter_)
                else library_id_iter_
            ),
            library_list
        ))

    # Check sample list
    if sample is not None:
        sample_list = [sample]
    if sample_list is not None:
        sample_orcabus_ids = list(map(
            lambda library_id_iter_: (
                library_id_iter_ if is_orcabus_ulid(library_id_iter_)
                else get_sample_orcabus_id_from_sample_id(library_id_iter_)
            ),
            sample_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each sample
                # Returns a list of lists
                list(map(
                    lambda sample_orcabus_id_iter_:
                    list_libraries_in_sample(sample_orcabus_id_iter_),
                    sample_orcabus_ids
                ))
            ))
        ))

    # Check subject list
    if subject is not None:
        subject_list = [subject]
    if subject_list is not None:
        subject_orcabus_ids = list(map(
            lambda subject_id_iter_: (
                subject_id_iter_ if is_orcabus_ulid(subject_id_iter_)
                else get_subject_orcabus_id_from_subject_id(subject_id_iter_)
            ),
            subject_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each subject
                list(map(
                    lambda subject_orcabus_id_iter_:
                    list_libraries_in_subject(subject_orcabus_id_iter_),
                    subject_orcabus_ids
                ))
            ))
        ))

    # Check individual list
    if individual is not None:
        individual_list = [individual]
    if individual_list is not None:
        individual_orcabus_ids = list(map(
            lambda individual_id_iter_: (
                individual_id_iter_ if is_orcabus_ulid(individual_id_iter_)
                else get_individual_orcabus_id_from_individual_id(individual_id_iter_)
            ),
            individual_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each individual
                list(map(
                    lambda individual_orcabus_id_iter_:
                    list_libraries_in_individual(individual_orcabus_id_iter_),
                    individual_orcabus_ids
                ))
            ))
        ))

    # Check project list
    if project is not None:
        project_list = [project]
    if project_list is not None:
        project_orcabus_ids = list(map(
            lambda project_id_iter_: (
                project_id_iter_ if is_orcabus_ulid(project_id_iter_)
                else get_project_orcabus_id_from_project_id(project_id_iter_)
            ),
            project_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each project
                list(map(
                    lambda project_orcabus_id_iter_:
                    list_libraries_in_project(project_orcabus_id_iter_),
                    project_orcabus_ids
                ))
            ))
        ))

    return library_list


# AWS Things
def get_sfn_client() -> 'SFNClient':
    return boto3.client('stepfunctions')


def get_ssm_client() -> 'SSMClient':
    return boto3.client('ssm')


def get_fastq_endpoint_url() -> str:
    return environ.get("FASTQ_BASE_URL") + "/api/v1/fastq"

def get_fastq_set_endpoint_url() -> str:
    return environ.get("FASTQ_BASE_URL") + "/api/v1/fastqSet"