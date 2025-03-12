#!/usr/bin/env python3

import re

# AWS PARAMETERS
METADATA_SUBDOMAIN_NAME = "metadata"

# API ENDPOINTS
LIBRARY_ENDPOINT = "api/v1/library"
SAMPLE_ENDPOINT = "api/v1/sample"
SUBJECT_ENDPOINT = "api/v1/subject"
PROJECT_ENDPOINT = "api/v1/project"
INDIVIDUAL_ENDPOINT = "api/v1/individual"
CONTACT_ENDPOINT = "api/v1/contact"

ORCABUS_ULID_REGEX_MATCH = re.compile(r'^(?:[a-z0-9]{3}\.)?[A-Z0-9]{26}$')
