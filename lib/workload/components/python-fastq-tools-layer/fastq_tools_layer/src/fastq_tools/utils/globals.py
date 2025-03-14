#!/usr/bin/env python3

import re

# AWS PARAMETERS
FASTQ_SUBDOMAIN_NAME = "fastq"

# API ENDPOINTS
FASTQ_LIST_ROW_ENDPOINT = "api/v1/fastq"
FASTQ_SET_ENDPOINT = "api/v1/fastqSet"

# REGEX
ORCABUS_ULID_REGEX_MATCH = re.compile(r'^[a-z0-9]{3}\.[A-Z0-9]{26}$')
