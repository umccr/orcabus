from django.db import transaction
from django.utils import timezone
import logging
import json
from io import StringIO

from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.models.sample_sheet import SampleSheet
from sequence_run_manager_proc.services.bssh_srv import BSSHService

from v2_samplesheet_maker.functions.v2_samplesheet_reader import v2_samplesheet_reader

logger = logging.getLogger(__name__)

def check_or_create_sequence_sample_sheet(payload: dict):
    """
    Check if the sample sheet for a sequence exists;
    if not, create it
    """
    sequence_run = Sequence.objects.get(sequence_run_id=payload["id"])
    if not sequence_run:
        logger.error(f"Sequence run {payload['id']} not found when checking or creating sequence sample sheet")
        raise ValueError(f"Sequence run {payload['id']} not found")
    
    return create_sequence_sample_sheet(sequence_run, payload)

@transaction.atomic
def create_sequence_sample_sheet(sequence: Sequence, payload: dict  ):
    """
    Create a sample sheet for a sequence
    """
    sample_sheet_name = payload.get("sampleSheetName")
    api_url = payload.get("apiUrl")
    
    bssh_srv = BSSHService()
    sample_sheet_content = bssh_srv.get_sample_sheet_from_bssh_run_files(api_url, sample_sheet_name)
    
    # Convert content to JSON format with v2_samplesheet_to_json function
    content_json = v2_samplesheet_reader(StringIO(sample_sheet_content))
    
    SampleSheet.objects.create(
        sequence=sequence,
        sample_sheet_name=sample_sheet_name,
        sample_sheet_content=json.dumps(content_json),
    )
