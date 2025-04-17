#!/usr/bin/env python3

import re
from enum import Enum
from os import environ

import typing

if typing.TYPE_CHECKING:
    from .models.job import JobPatch

# Add context prefix - fastq list row
FQLR_CONTEXT_PREFIX = "fqr"  # Fastq List Row
UNARCHIVE_FASTQ_JOB_PREFIX = "ufj"  # Unarchive Job Prefix

# https://regex101.com/r/zJRC62/1
ORCABUS_ULID_REGEX_MATCH = re.compile(r'^[a-z0-9]{3}\.[A-Z0-9]{26}$')

DEFAULT_ROWS_PER_PAGE = 100

# Envs
EVENT_BUS_NAME_ENV_VAR = "EVENT_BUS_NAME"
EVENT_SOURCE_ENV_VAR = "EVENT_SOURCE"
EVENT_DETAIL_TYPE_CREATE_JOB_ENV_VAR = "EVENT_DETAIL_TYPE_CREATE_JOB"
EVENT_DETAIL_TYPE_UPDATE_JOB_ENV_VAR = "EVENT_DETAIL_TYPE_UPDATE_JOB"
UNARCHIVING_JOB_STATE_MACHINE_ARN_ENV_VAR = "UNARCHIVING_JOB_STATE_MACHINE_ARN"


# Event enums
class JobEventDetailTypeEnum(Enum):
    CREATE = environ[EVENT_DETAIL_TYPE_CREATE_JOB_ENV_VAR]
    UPDATE = environ[EVENT_DETAIL_TYPE_UPDATE_JOB_ENV_VAR]


def get_default_job_patch_entry() -> 'JobPatch':
    from .models.job import JobPatch
    from .models import JobStatus
    return JobPatch(**dict({"status": JobStatus.RUNNING}))