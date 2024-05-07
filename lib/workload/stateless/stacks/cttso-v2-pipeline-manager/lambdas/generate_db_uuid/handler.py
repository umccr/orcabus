#!/usr/bin/env python3

"""
Generate a random uuid via the uuid7 module
'018e83b0-ca5d-7be7-aeb6-28fc75038316'
These are time-based UUIDs, with the timestamp encoded in the first 48 bits.
"""

from uuid6 import uuid7


def handler(event, context):
    return {
        "db_uuid": str(uuid7())
    }
