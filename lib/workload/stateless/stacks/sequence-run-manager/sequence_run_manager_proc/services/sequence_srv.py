import logging

from typing import Dict, Optional
from django.db import transaction

from sequence_run_manager.models.sequence import Sequence, SequenceStatus
from sequence_run_manager.models.state import State
from sequence_run_manager_proc.domain.sequence import SequenceDomain
from sequence_run_manager_proc.services.bssh_srv import BSSHService

# from data_processors.pipeline.tools import liborca

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SequenceConfig:
    GDS_URI_SCHEME = "gds://"
    UNKNOWN_VALUE = "UNKNOWN"


@transaction.atomic
def create_or_update_sequence_from_bssh_event(payload: dict) -> SequenceDomain:
    """
    Payload dict is sourced from BSSH Run event
    Here, we map BSSH event body attributes to our Sequence model

    BSSH event body has the following JSON content
    NOTE: values are mocked

    {
        "gdsFolderPath": "/Runs/200508_A01052_0001_BH5LY7ACGT_r.ACGTlKjDgEy099ioQOeOWg",
        "gdsVolumeName": "bssh.acgtacgt498038ed99fa94fe79523959",
        "reagentBarcode": "NV9999999-RGSBS",
        "v1pre3Id": "unknown",
        "dateModified": "2022-06-24T05:07:53.476767Z",
        "acl": [
            "wid:<uuid4_string>",
            "tid:<82_char_string>"
        ],
        "flowcellBarcode": "BARCODEEE",
        "icaProjectId": "123456-6789-aaaa-bbbb-abcdefghijk",
        "sampleSheetName": "SampleSheet.csv",
        "apiUrl": "https://api.aps2.sh.basespace.illumina.com/v2/runs/r.ACGTlKjDgEy099ioQOeOWg",
        "name": "200508_A01052_0001_BH5LY7ACGT",
        "id": "r.ACGTlKjDgEy099ioQOeOWg",
        "instrumentRunId": "200508_A01052_0001_BH5LY7ACGT",
        "status": "PendingAnalysis"
    }
    """

    try:
        # mandatory
        run_id = payload.get("id")
        date_modified = payload["dateModified"]
        state = payload["status"] # for recording state changes
        status: SequenceStatus = SequenceStatus.from_seq_run_status(payload["status"])
        
        # calculate timing info
        timing_info = calculate_timing_info(date_modified, status)

        # flag to show if new sequence is created
        is_new_sequence = False

        # get or create sequence
        sequence = Sequence.objects.filter(sequence_run_id=run_id).first()
    
        if not sequence:
            is_new_sequence = True
            sequence = create_new_sequence(run_id, payload, status, timing_info)
        else:
            sequence = update_existing_sequence(sequence, payload)

        # create sequence domain
        sequence_domain = create_sequence_domain(sequence, status, timing_info, is_new_sequence, state)
        return sequence_domain  
    
    except Exception as e:
        logger.error(f"Error creating or updating sequence: {e}")
        raise e
    
def calculate_timing_info(date_modified: str, status: SequenceStatus) -> Dict[str, Optional[str]]:
    """Calculate start and end times based on status"""
    return {
        'start_time': date_modified,
        'end_time': date_modified if SequenceStatus.is_terminal(status) else None
    }

def create_new_sequence(run_id: str, payload: Dict, status: SequenceStatus, timing_info: Dict) -> Sequence:
    """Create a new sequence record"""
    logger.info(f"Creating new Sequence (sequence_run_id={run_id})")
    
    sequence = Sequence(
        sequence_run_id=run_id,
        status=status,
        start_time=timing_info['start_time'],
        end_time=timing_info['end_time'],
        run_volume_name=payload.get("gdsVolumeName"),
        run_folder_path=payload.get("gdsFolderPath"),
        run_data_uri=f"{SequenceConfig.GDS_URI_SCHEME}{payload.get('gdsVolumeName')}{payload.get('gdsFolderPath')}",
        reagent_barcode=payload.get("reagentBarcode"),
        sample_sheet_name=payload.get("sampleSheetName"),
        v1pre3_id=payload.get("v1pre3Id"),
        ica_project_id=payload.get("icaProjectId"),
        api_url=payload.get("apiUrl"),
        # optional fields when 'Uploading' stage
        instrument_run_id=payload.get("instrumentRunId", SequenceConfig.UNKNOWN_VALUE), 
        flowcell_barcode=payload.get("flowcellBarcode", SequenceConfig.UNKNOWN_VALUE),
        sequence_run_name=payload.get("name", SequenceConfig.UNKNOWN_VALUE),
    )
    
    if payload.get("apiUrl"):
        enrich_sequence_with_run_details(sequence, payload["apiUrl"])
    
    sequence.save()
    logger.info(f"Created new Sequence (sequence_run_id={run_id}, status={status.value})")
    return sequence

def enrich_sequence_with_run_details(sequence: Sequence, api_url: str) -> None:
    """
    Fetch and add run details from BSSH API
    Note: currently only experiment name is fetched, more details can be added here
    """
    bssh_service = BSSHService()
    run_details = bssh_service.get_run_details(api_url)
    sequence.experiment_name = run_details.get("ExperimentName")
    logger.info(f"Enriched Sequence (sequence_run_id={sequence.sequence_run_id}, experiment_name={sequence.experiment_name})")
    
def update_existing_sequence(sequence: Sequence, payload: Dict) -> Sequence:
    """Update an existing sequence record"""
    # Update basic fields if they were UNKNOWN
    if sequence.instrument_run_id == SequenceConfig.UNKNOWN_VALUE and payload.get("instrumentRunId"):
        sequence.instrument_run_id = payload.get("instrumentRunId", SequenceConfig.UNKNOWN_VALUE)
        sequence.sequence_run_name = payload.get("name", SequenceConfig.UNKNOWN_VALUE)
        sequence.flowcell_barcode = payload.get("flowcellBarcode", SequenceConfig.UNKNOWN_VALUE)
    
    logger.info(f"Updating Sequence successfully (sequence_run_id={sequence.sequence_run_id}, instrument_run_id={sequence.instrument_run_id})")
    
    sequence.save()
    return sequence

def create_sequence_domain(sequence: Sequence, status: SequenceStatus, timing_info: Dict, is_new_sequence: bool, state: str) -> SequenceDomain:
    """Create SequenceDomain with change tracking"""
    status_changed = is_new_sequence or sequence.status != status.value
    
    logger.info(f"Creating SequenceDomain (sequence_run_id={sequence.sequence_run_id}, status={status.value}, new_sequence_created={is_new_sequence})")
    # update status and end time if status has changed
    if status_changed:
        logger.info(f"Updating Sequence status (sequence_run_id={sequence.sequence_run_id}, status={status.value})")
        sequence.status = status
        sequence.end_time = timing_info['end_time']
        sequence.save()

    # check if state exists
    state_exists = State.objects.filter(sequence=sequence,timestamp=timing_info['start_time'],status=state).exists()
    
    return SequenceDomain(
        sequence=sequence,
        status_has_changed=status_changed,
        state_has_changed=not state_exists
    )
