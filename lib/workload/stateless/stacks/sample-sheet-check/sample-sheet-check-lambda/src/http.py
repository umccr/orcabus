import json
from typing import Literal


def construct_body(check_status: Literal["PASS", "FAIL"], error_message: str = '', log_path='',
                   v2_sample_sheet: str = ''):
    """
    Parameters
    ----------
    check_status : One of 'PASS' or 'FAIL'

    error_message : The error message to return
    log_path : The path to the log file

    v2_sample_sheet : The string representation of the v2 samplesheet

    Return
    ----------
    error_message : str
        any error message that stops the check
    """

    body = {
        "check_status": check_status,
        "error_message": error_message,
        "v2_sample_sheet": v2_sample_sheet
    }

    if log_path:
        # Get Log Data
        with open(log_path, 'r') as log_file:
            log_text = log_file.read()

        body["log_file"] = log_text

    return json.dumps(body)


def construct_response(status_code, body, origin: str):
    """Construct response from parameter"""

    if not origin.endswith('umccr.org'):
        origin = 'https://umccr.org'

    response = {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Content-Type': 'application/json',
        },
    }

    if body:
        response['body'] = body

    return response
