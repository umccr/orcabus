#!/usr/bin/env python3

"""
Getting the payload helpers
"""
from typing import Dict

from workflow_tools.utils.globals import PAYLOAD_ENDPOINT
from workflow_tools.utils.requests_helpers import get_request_results


def get_payload(payload_id: str) -> Dict:
    """
    Get subject from the subject id
    :param contact_id:
    :return:
    """
    # Get subject
    return get_request_results(PAYLOAD_ENDPOINT, payload_id)