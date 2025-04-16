#!/usr/bin/env python3

import re
from enum import Enum

# AWS PARAMETERS
DATA_SHARING_SUBDOMAIN_NAME = "data-sharing"

# API ENDPOINTS
PACKAGING_ENDPOINT = "api/v1/package"
PUSH_JOB_ENDPOINT = "api/v1/push"

# REGEX
ORCABUS_ULID_REGEX_MATCH = re.compile(r'^[a-z0-9]{3}\.[A-Z0-9]{26}$')


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    SUCCEEDED = "SUCCEEDED"

