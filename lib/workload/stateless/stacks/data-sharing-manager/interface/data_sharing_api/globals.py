#!/usr/bin/env python3

import re
from enum import Enum
from os import environ

import typing

if typing.TYPE_CHECKING:
    from .models import JobPatch
    from .models.package import PackageCreate
    from .models.push import PushLocationBody

# Add context prefix - fastq list row
PACKAGE_CONTEXT_PREFIX = 'pkg'
PUSH_JOB_CONTEXT_PREFIX = 'psh'

# https://regex101.com/r/zJRC62/1
ORCABUS_ULID_REGEX_MATCH = re.compile(r'^[a-z0-9]{3}\.[A-Z0-9]{26}$')

DEFAULT_ROWS_PER_PAGE = 100

# Envs
EVENT_BUS_NAME_ENV_VAR = "EVENT_BUS_NAME"
EVENT_SOURCE_ENV_VAR = "EVENT_SOURCE"
EVENT_DETAIL_TYPE_CREATE_PACKAGE_JOB_ENV_VAR = "EVENT_DETAIL_TYPE_CREATE_PACKAGE_JOB"
EVENT_DETAIL_TYPE_UPDATE_PACKAGE_JOB_ENV_VAR = "EVENT_DETAIL_TYPE_UPDATE_PACKAGE_JOB"
EVENT_DETAIL_TYPE_CREATE_PUSH_JOB_ENV_VAR = "EVENT_DETAIL_TYPE_CREATE_PUSH_JOB"
EVENT_DETAIL_TYPE_UPDATE_PUSH_JOB_ENV_VAR = "EVENT_DETAIL_TYPE_UPDATE_PUSH_JOB"
PACKAGE_JOB_STATE_MACHINE_ARN_ENV_VAR = "PACKAGE_JOB_STATE_MACHINE_ARN"
PRESIGN_STATE_MACHINE_ARN_ENV_VAR = "PRESIGN_STATE_MACHINE_ARN"
PUSH_JOB_STATE_MACHINE_ARN_ENV_VAR = "PUSH_JOB_STATE_MACHINE_ARN"
PACKAGE_BUCKET_NAME_ENV_VAR = "PACKAGE_BUCKET_NAME"

# Event enums
class PackageEventDetailTypeEnum(Enum):
    CREATE = environ[EVENT_DETAIL_TYPE_CREATE_PACKAGE_JOB_ENV_VAR]
    UPDATE = environ[EVENT_DETAIL_TYPE_UPDATE_PACKAGE_JOB_ENV_VAR]


class PushEventDetailTypeEnum(Enum):
    CREATE = environ[EVENT_DETAIL_TYPE_CREATE_PUSH_JOB_ENV_VAR]
    UPDATE = environ[EVENT_DETAIL_TYPE_UPDATE_PUSH_JOB_ENV_VAR]


def get_default_job_patch_entry() -> 'JobPatch':
    from .models import JobPatch, JobStatus
    return JobPatch(**dict({"status": JobStatus.RUNNING}))


def get_default_package_create_entry() -> 'PackageCreate':
    from .models.package import PackageCreate
    return PackageCreate(**dict({
        "packageName": "package-name",
        "packageRequest": {
            "libraryList": ["L12345678"],
            "dataType": ["FASTQ"]
        }
    }))


def get_default_push_location_body_entry() -> 'PushLocationBody':
    from .models.push import PushLocationBody
    return PushLocationBody(**dict({"shareDestination": "s3://bucket/path/to/destination/"}))

