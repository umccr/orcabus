#!/usr/bin/env python

"""
Very straightforward step function, expect event detail to contain
instrumentRunId, converted to instrument_run_id,

This could get more complex in the future

"""

from typing import Dict


def handler(event, context) -> Dict:
    return {
        "instrument_run_id": event.get("instrumentRunId")
    }
