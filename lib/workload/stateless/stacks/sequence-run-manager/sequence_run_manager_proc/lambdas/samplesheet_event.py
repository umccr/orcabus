import os

import django

django.setup()

# --- keep ^^^ at top of the module

import logging

from sequence_run_manager_proc.services import sample_sheet_srv
from libumccr import libjson
from libumccr.aws import libeb
# from libica.app import ENSEventType

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def event_handler(event, context):
    """
    This lambda function is used to handle the sample sheet event from the event bus
    
    event payload dict
    {
    "version": "0",
    "id": "12345678-90ab-cdef-1234-567890abcdef",
    "detail-type": "SequenceRunSampleSheetChange",
    "source": "orcabus.sequencerunmanager",
    "account": "000000000000",
    "time": "2025-03-00T00:00:00Z",
    "region": "ap-southeast-2",
    "resources": [],
    "detail": {
        "instrumentRunId": "250328_A01052_0258_AHFGM7DSXF",
        "sequenceRunId": "r.1234567890abcdefghijklmn", // fake sequence run id
        "sequenceOrcabusId": "seq.1234567890ABCDEFGHIJKLMN", // orcabusid for the sequence run (fake run)
        "timeStamp": "2025-03-01T00:00:00.000000+00:00",
        "sampleSheetName": "sampleSheet_v2.csv",
        "samplesheetbase64gz": "base64_encoded_samplesheet........"
        }
    }
    """
    logger.info(f"Received event: {event}")
    logger.info(f"Received context: {context}")
    logger.info(libjson.dumps(event))
    logger.info("Start processing sample sheet event ....")

    sample_sheet_srv.check_or_create_sequence_sample_sheet_from_event(event["detail"])
