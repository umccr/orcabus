import os
import logging
import json
from datetime import datetime
from libumccr.aws import libeb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def emit_srm_api_event(event):
    """
    Emit events to the event bridge sourced from the sequence run manager API
    
    so far we only support SRSSC and SRLLC events, examples:
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
        "samplesheetbase64gz": "base64_encoded_samplesheet........",
        "comment":{
            "comment": "comment",
            "created_by": "user",
            "created_at": "2025-03-01T00:00:00.000000+00:00"
        }
        }
    }
    {
    "version": "0",
    "id": "12345678-90ab-cdef-1234-567890abcdef",
    "detail-type": "SequenceRunLibraryLinkingChange",
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
        "linkedLibraries": [
                "L2000000",
                "L2000001",
                "L2000002"
            ],
        "comment":{
            "comment": "comment",
            "created_by": "user",
            "created_at": "2025-03-01T00:00:00.000000+00:00"
        }
        }
    }
    """
    # check environment variables
    assert os.environ.get("EVENT_BUS_NAME", None) is not None, "EVENT_BUS_NAME is not set"
    assert event["eventType"] in ["SequenceRunSampleSheetChange", "SequenceRunLibraryLinkingChange"], "Unsupported event type"
    
    # construct event
    source = "orcabus.sequencerunmanagerapi"
    event_bus_name = os.environ.get("EVENT_BUS_NAME", None)
    
    if event_bus_name is None:
        logger.error("EVENT_BUS_NAME is not set")
        return
    
    if event["eventType"] == "SequenceRunSampleSheetChange":
        event_type = "SequenceRunSampleSheetChange"
        detail_type = "SequenceRunSampleSheetChange"
        source = "orcabus.sequencerunmanagerapi"
        detail = {
            "instrumentRunId": event["instrumentRunId"],
            "sequenceRunId": event["sequenceRunId"],
            "sequenceOrcabusId": event["sequenceOrcabusId"],
            "timeStamp": datetime.now(),
            "sampleSheetName": event["sampleSheetName"],
            "samplesheetbase64gz": event["samplesheetbase64gz"],
            "comment": {
                "comment": event["comment"]["comment"],
                "created_by": event["comment"]["created_by"],
                "created_at": event["comment"]["created_at"]
            }
        }
    
    elif event["eventType"] == "SequenceRunLibraryLinkingChange":
        event_type = "SequenceRunLibraryLinkingChange"
        detail_type = "SequenceRunLibraryLinkingChange"
        source = "orcabus.sequencerunmanagerapi"
        detail = {
            "instrumentRunId": event["instrumentRunId"],
            "sequenceRunId": event["sequenceRunId"],
            "sequenceOrcabusId": event["sequenceOrcabusId"],
            "timeStamp": datetime.now(),
            "linkedLibraries": event["linkedLibraries"],
        }
    
    else:
        logger.error(f"Unsupported event type: {event['eventType']}")
        return
    
    response = libeb.emit_event({
        "Source": source,
        "DetailType": detail_type,
        "Detail": json.dumps(detail),
        "EventBusName": event_bus_name,
    })
    
    logger.info(f"Sent a {event_type} event to event bus {event_bus_name}:")
    logger.info(event)
    logger.info(f"{__name__} done.")
    return response
    
    
    