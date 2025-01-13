import base64
import tempfile
import logging
from email.parser import BytesParser

from src.checker import construct_sample_sheet, run_sample_sheet_content_check, run_sample_sheet_check_with_metadata
from src.http import construct_body, construct_response
from src.logger import set_logger
from src.v2_samplesheet_builder import v1_to_v2_samplesheet

# Logging
LOG_PATH = "/tmp/samplesheet_check.log"
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Parameters
    ----------
    event : Object
        An object of payload pass through the lambda
    context : Object
        An aws resource information

    """
    logger.info(f"Processing (event, context): {event}, {context}")

    # Parse header
    headers = event.get("headers", {})
    origin = headers.get("origin", "")
    authorization = headers.get("Authorization", headers.get("authorization", ""))
    content_type = headers.get('Content-Type', headers.get('content-type', ''))

    # Parse body payload
    if event.get("isBase64Encoded", False):
        body = base64.b64decode(event["body"])
    else:
        body = event["body"].encode()
    ct = f"Content-Type: {content_type}\n\n".encode()
    msg = BytesParser().parsebytes(ct + body)
    if not msg.is_multipart():
        body = construct_body(check_status="FAIL", error_message="Invalid body",
                              v2_sample_sheet='')
        response = construct_response(status_code=400, body=body, origin=origin)
        return response

    multipart_content = {}
    for part in msg.get_payload():
        multipart_content[part.get_param(
            'name', header='content-disposition')] = part.get_payload(decode=True)

    file_data = multipart_content["file"]
    log_level = multipart_content["logLevel"].decode("utf-8")

    # Save file to temp file
    temporary_data = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    temporary_data.write(file_data.decode("utf-8"))
    temporary_data.seek(0)

    # Setup Logging
    set_logger(log_path=LOG_PATH, log_level=log_level)

    try:
        # Construct and run sample sheet checker
        sample_sheet = construct_sample_sheet(temporary_data.name)
        run_sample_sheet_content_check(sample_sheet)
        run_sample_sheet_check_with_metadata(sample_sheet, authorization)

        # run sample sheet v2 conversion
        v2_sample_sheet_str = v1_to_v2_samplesheet(sample_sheet)

    except Exception as e:
        body = construct_body(check_status="FAIL", error_message=str(e), log_path=LOG_PATH,
                              v2_sample_sheet='')
        response = construct_response(status_code=400, body=body, origin=origin)
        return response

    body = construct_body(check_status='PASS', log_path=LOG_PATH, v2_sample_sheet=v2_sample_sheet_str)
    response = construct_response(status_code=200, body=body, origin=origin)
    return response
