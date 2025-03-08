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
    
    # get sequence by sequence_run_id
    sequence = Sequence.objects.get(sequence_run_id=payload["id"])
    
    # None by default
    comment = None
    
    State.objects.create(status=status, timestamp=timestamp, sequence=sequence, comment=comment)
    logger.info(f"Created new Sequence State (sequence_run_id={sequence.sequence_run_id}, status={status})")