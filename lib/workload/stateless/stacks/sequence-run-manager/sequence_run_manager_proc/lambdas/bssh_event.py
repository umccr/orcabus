import os

import django

django.setup()

# --- keep ^^^ at top of the module

import logging

from sequence_run_manager_proc.domain.sequence import (
    SequenceDomain,
    SequenceRule,
    SequenceRuleError,
)
from sequence_run_manager_proc.services import sequence_srv, sequence_state_srv, sequence_library_srv

from libumccr import libjson
from libumccr.aws import libeb
# from libica.app import ENSEventType

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# IMPLEMENTED_ENS_TYPES = [
#     ENSEventType.BSSH_RUNS.value,
# ]

# PRODUCED_BY_BSSH = ["BaseSpaceSequenceHub"]


def event_handler(event, context):
    """event payload dict

    Here is how to generate an example event. See README for more.
        python manage.py generate_mock_bssh_event | jq
        
    example event:
    {
    "version": "0",
    "id": f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454",  # Random UUID
    "detail-type": "Event from aws:sqs",
    "source": "Pipe IcaEventPipeConstru-xxxxxxxx",
    "account": "444444444444",
    "time": "2024-11-02T21:58:22Z",
    "region": "ap-southeast-2",
    "resources": [],
    "detail": {
        "ica-event": {
            "gdsFolderPath": "",
            "gdsVolumeName": "bssh.123456789fabcdefghijkl",
            "v1pre3Id": "444555555555",
            "dateModified": "2024-11-02T21:58:13.7451620Z",
            "acl": [
                "wid:12345678-debe-3f9f-8b92-21244f46822c",
                "tid:Yxmm......"
            ],
            "flowcellBarcode": "HVJJJJJJ",
            "icaProjectId": "12345678-53ba-47a5-854d-e6b53101adb7",
            "sampleSheetName": "SampleSheet.V2.134567.csv",
            "apiUrl": "https://api.aps2.sh.basespace.illumina.com/v2/runs/r.4Wz-ABCDEFGHIJKLM-A",
            "name": "222222_A01052_1234_BHVJJJJJJ",
            "id": "r.4Wz-ABCDEFGHIJKLMN-A",
            "instrumentRunId": "222222_A01052_1234_BHVJJJJJJ",
            "status": "PendingAnalysis"
            }
        }
    }

    This Lambda is to be subscribed to Orcabus Eventbridge rule for BSSH event through ICA v2 sqs event pipe
    https://help.ica.illumina.com/project/p-notifications#delivery-targets
    https://illumina.gitbook.io/ica-v1/events/e-deliverytargets (deprecated)

    OrcaBus SRM BSSH Event High Level:
        - through ICA v2 sqs event pipe, we subscribe to Orcabus Eventbridge with specific rule
        - this Lambda is to be hooked to this Eventbridge rule to process the event
        - now, when `ica-event` event with `instrumentRunId` and `statuschanged` status arrive...
            - we parse these `ica-event` payload, transform and persist them into our internal OrcaBus SRM `Sequence` entity model
            - after persisted into database, we again transform into our internal `SequenceRunStateChange` domain event
            - this domain event schema is what we consented and published in our EventBus event schema registry
            - we then dispatch our domain events into the channel in batching manner for efficiency
        - challenge:
            - upstream ICA ENS may deliver multiple duplicated `bssh.runs` events of the same `statuschanged`
            - at upstream end, their service guarantee that -- at-least-once delivery -- distributed computing semantic
            - it is up to downstream subscriber to handle this
            - here, we are using implicit RDBMS feature to herding these events back into
              unique, consistent record -- based on our internal business entity logic constraint

    :param event:
    :param context:
    :return:
    """
    assert os.environ["EVENT_BUS_NAME"] is not None, "EVENT_BUS_NAME must be set"
    
    logger.info("Start processing BSSH ENS event")
    logger.info(libjson.dumps(event))

    event_bus_name = os.environ["EVENT_BUS_NAME"]

    # Extract relevant fields from the event payload
    event_details = event.get("detail", {}).get("ica-event", {})

    # Create or update Sequence record from BSSH Run event payload
    sequence_domain: SequenceDomain = (
        sequence_srv.create_or_update_sequence_from_bssh_event(event_details)
    )
    entry = None

    # Create SequenceRunState record from BSSH Run event payload
    # Check or create sequence run libraries linking when state changes
    if sequence_domain.state_has_changed:
        sequence_state_srv.create_sequence_state_from_bssh_event(event_details)
        sequence_library_srv.check_or_create_sequence_run_libraries_linking(event_details)

    # Detect SequenceRunStatusChange
    if sequence_domain.status_has_changed:
        try:
            SequenceRule(sequence_domain.sequence).must_not_emergency_stop()
            entry = sequence_domain.to_put_events_request_entry(
                    event_bus_name=event_bus_name,
            )
                    
        except SequenceRuleError as se:
            # FIXME emit custom event for this? something to tackle later. log & skip for now
            reason = f"Aborted pipeline due to {se}"
            logger.warning(reason)

    # Dispatch event entry using libeb.
    if entry:
        libeb.emit_event(entry)

    resp_msg = {
        "message": f"BSSH ENS event processing complete",
    }
    logger.info(libjson.dumps(resp_msg))
    return resp_msg
