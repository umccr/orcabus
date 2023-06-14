import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sequence_run_manager.settings.base")
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
from libica.app import ENSEventType

logger = logging.getLogger()
logger.setLevel(logging.INFO)

IMPLEMENTED_ENS_TYPES = [
    ENSEventType.BSSH_RUNS.value,
]

PRODUCED_BY_BSSH = ["BaseSpaceSequenceHub"]


def sqs_handler(event, context):
    """event payload dict

    This Lambda is to be subscribed to SQS for BSSH event through ICA v1 ENS
    https://illumina.gitbook.io/ica-v1/events/e-deliverytargets

    :param event:
    :param context:
    :return:
    """
    logger.info("Start processing BSSH ENS event")
    logger.info(libjson.dumps(event))

    messages = event["Records"]

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
            seq_domain: SequenceDomain = (
                sequence_srv.create_or_update_sequence_from_bssh_event(payload)
            )

            # Detect SequenceRunStateChange
            if seq_domain.state_has_changed:
                try:
                    SequenceRule(seq_domain.sequence).must_not_emergency_stop()
                    # TODO
                    #  generate SequenceRunStateChange code binding
                    #  emit event to bus
                except SequenceRuleError as se:
                    reason = f"Aborted pipeline. {se}"
                    logger.warning(reason)
                    return {"message": reason}

    resp_msg = {"message": f"BSSH ENS event processing complete"}
    logger.info(libjson.dumps(resp_msg))
    return resp_msg
