import logging

from django.db import transaction
from django.db.models import QuerySet

from sequence_run_manager.models.sequence import Sequence, SequenceStatus
from sequence_run_manager.models.state import State


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@transaction.atomic
def create_sequence_state_from_bssh_event(payload: dict) -> None:
    """
    Create SequenceState record from BSSH Run event payload
    
    {
        "dateModified": "2022-06-24T05:07:53.476767Z",
        "instrumentRunId": "200508_A01052_0001_BH5LY7ACGT",
        "status": "PendingAnalysis"
        ...
    }
    """
    status = payload["status"]
    timestamp = payload["dateModified"]
    
    # get sequence by instrument_run_id
    instrument_run_id = payload["instrumentRunId"]
    sequence = Sequence.objects.get(instrument_run_id=instrument_run_id)
    
    # None by default
    comment = None
    
    # sequence status in SUCCEEDED: 
    # if transition from STARTED to SUCCEEDED, set comment to "Sequence complete"
    # if transition from FAILED to SUCCEEDED, set comment to "Conversion re-triggered, and sequence completed.'
    if sequence.status == SequenceStatus.SUCCEEDED:
        previous_state = State.objects.filter(sequence=sequence).order_by('-timestamp').first()
        if previous_state is not None and SequenceStatus.from_seq_run_status(previous_state.status) == SequenceStatus.STARTED:
            comment = "Sequence completed. Now in state " + status + " ."
        if previous_state is not None and SequenceStatus.from_seq_run_status(previous_state.status) == SequenceStatus.FAILED:
            comment = "Conversion re-triggered, and sequence completed. Now in state " + status + " ."

    # sequence status in FAILED:
    # if transition from SUCCEEDED to FAILED, set comment to "Sequence completed. But failed in post analysis process."
    # if transition from STARTED to FAILED, set comment to "Sequence failed. Now in state " + status + " ."
    if sequence.status == SequenceStatus.FAILED:
        previous_state = State.objects.filter(sequence=sequence).order_by('-timestamp').first()
        if previous_state is not None and SequenceStatus.from_seq_run_status(previous_state.status) == SequenceStatus.SUCCEEDED:
            comment = "Sequence completed. But failed in post analysis process."
        else:
            comment = "Sequence failed. Now in state " + status + " ."
    
    State.objects.create(status=status, timestamp=timestamp, sequence=sequence, comment=comment)