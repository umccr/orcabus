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
from sequence_run_manager_proc.services import sequence_srv

from libumccr import libjson
from libumccr.aws import libeb
from libica.app import ENSEventType

logger = logging.getLogger()
logger.setLevel(logging.INFO)

IMPLEMENTED_ENS_TYPES = [
    ENSEventType.BSSH_RUNS.value,
]

PRODUCED_BY_BSSH = ["BaseSpaceSequenceHub"]


def sqs_handler(event, context):
    """event payload dict

    Here is how to generate an example event. See README for more.
        python manage.py generate_mock_bssh_event | jq

    This Lambda is to be subscribed to SQS for BSSH event through ICA v1 ENS
    https://illumina.gitbook.io/ica-v1/events/e-deliverytargets

    OrcaBus SRM BSSH Event High Level:
        - through ICA v1 ENS, we subscribe to `bssh.runs` using SQS queue created at our AWS
        - in our SQS queue, we hook this Lambda as event trigger and process the event
        - now, when `bssh.runs` event with `statuschanged` status arrive...
            - this SQS event envelope may contain multiple `Records`
            - we parse these `Records`, transform and persist them into our internal OrcaBus SRM `Sequence` entity model
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
    logger.info("Start processing BSSH ENS event")
    logger.info(libjson.dumps(event))

    messages = event["Records"]
    event_bus_name = os.environ["EVENT_BUS_NAME"]

    entries = list()

    for message in messages:
        event_type = message["messageAttributes"]["type"]["stringValue"]
        produced_by = message["messageAttributes"]["producedby"]["stringValue"]

        if event_type not in IMPLEMENTED_ENS_TYPES:
            logger.warning(f"Skipping unsupported ENS type: {event_type}")
            continue

        if produced_by not in PRODUCED_BY_BSSH:
            raise ValueError(f"Unrecognised BSSH event produced_by: {produced_by}")

        if event_type == ENSEventType.BSSH_RUNS.value:
            payload = {}
            payload.update(libjson.loads(message["body"]))

            # Create or update Sequence record from BSSH Run event payload
            sequence_domain: SequenceDomain = (
                sequence_srv.create_or_update_sequence_from_bssh_event(payload)
            )

            # Detect SequenceRunStateChange
            if sequence_domain.state_has_changed:
                try:
                    SequenceRule(sequence_domain.sequence).must_not_emergency_stop()
                    entry = sequence_domain.to_put_events_request_entry(
                        event_bus_name=event_bus_name,
                    )
                    entries.append(entry)
                except SequenceRuleError as se:
                    # FIXME emit custom event for this? something to tackle later. log & skip for now
                    reason = f"Aborted pipeline due to {se}"
                    logger.warning(reason)
                    continue

    # Dispatch all event entries in one-go! libeb will take care of batching them up for efficiency.
    if entries:
        libeb.dispatch_events(entries)

    resp_msg = {
        "message": f"BSSH ENS event processing complete",
    }
    logger.info(libjson.dumps(resp_msg))
    return resp_msg
