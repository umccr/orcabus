#!/usr/bin/env python3

import re

# Add context prefix
CONTEXT_PREFIX = "fqr"

# https://regex101.com/r/zJRC62/1
ORCABUS_ULID_REGEX_MATCH = re.compile(r'^[a-z0-9]{3}\.[A-Z0-9]{26}$')
