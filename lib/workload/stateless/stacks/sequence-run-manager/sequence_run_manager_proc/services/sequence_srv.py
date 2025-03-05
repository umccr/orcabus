import logging

from django.db import transaction
from django.db.models import QuerySet

from sequence_run_manager.models.sequence import Sequence, SequenceStatus
from sequence_run_manager.models.state import State
from sequence_run_manager_proc.domain.sequence import SequenceDomain
from sequence_run_manager_proc.services.sequence_library_srv import create_sequence_run_libraries_linking
from sequence_run_manager_proc.services.bssh_srv import BSSHService
from sequence_run_manager_proc.services.sequence_library_srv import create_sequence_run_libraries_linking
from sequence_run_manager_proc.services.bssh_srv import BSSHService
# from data_processors.pipeline.tools import liborca

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GDS_URI_SCHEME = "gds://"


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

    # mandatory
    run_id = payload.get("id")
    date_modified = payload["dateModified"]

    # status must exist in payload
    status: SequenceStatus = SequenceStatus.from_seq_run_status(payload["status"])

    # derive start_time and end_time from date_modified and status
    start_time = date_modified
    end_time = None
    if status in [
        SequenceStatus.SUCCEEDED,
        SequenceStatus.FAILED,
        SequenceStatus.ABORTED,
    ]:
        end_time = date_modified

    # look up existing Sequence record from db
    qs: QuerySet = Sequence.objects.filter(sequence_run_id=run_id)

    if not qs.exists():
        logger.info(f"Creating new Sequence (sequence_run_id={run_id})")

        seq = Sequence()
        
        seq.sequence_run_id = run_id
        seq.status = status
        seq.start_time = start_time
        seq.end_time = end_time
        
        seq.instrument_run_id = payload.get("instrumentRunId")
        seq.run_volume_name = payload.get("gdsVolumeName")
        seq.run_folder_path = payload.get("gdsFolderPath")
        seq.run_data_uri = f"{GDS_URI_SCHEME}{payload.get("gdsVolumeName")}{payload.get("gdsFolderPath")}"
        seq.reagent_barcode = payload.get("reagentBarcode")
        seq.flowcell_barcode = payload.get("flowcellBarcode")
        seq.sample_sheet_name = payload.get("sampleSheetName")
        
        seq.sequence_run_name = payload.get("name")
        
        seq.v1pre3_id = payload.get("v1pre3Id")
        seq.ica_project_id = payload.get("icaProjectId")
        seq.api_url = payload.get("apiUrl")
        
        # get run details from bssh srv api call
        bssh_service = BSSHService()
        run_details = bssh_service.get_run_details(payload.get("apiUrl"))
        # get experiment name from bssh run details
        seq.experiment_name = run_details.get("ExperimentName", None)
        
        # seq.sample_sheet_config = liborca.get_samplesheet_json_from_file(
        #     gds_volume=gds_volume_name,
        #     samplesheet_path=f"{gds_folder_path}/{sample_sheet_name}"
        # )
        # seq.run_config = liborca.get_run_config_from_runinfo(
        #     gds_volume=gds_volume_name,
        #     runinfo_path=f"{gds_folder_path}/RunInfo.xml"
        # )

        seq.save()
        
        logger.info(
            f"Created new Sequence (sequence_run_id={run_id}, status={status.value})"
        )
        return SequenceDomain(sequence=seq, status_has_changed=True, state_has_changed=True)
    else:
        seq: Sequence = qs.get()
        seq_domain = SequenceDomain(sequence=seq)

        if seq.status != status.value:
            logger.info(
                f"Updating Sequence (sequence_run_id={run_id}, status={status.value})"
            )
            seq.status = status
            seq.end_time = end_time
            seq.save()
            logger.info(
                f"Updated Sequence (sequence_run_id={run_id}, status={status.value})"
            )
            seq_domain.status_has_changed = True
        else:
            logger.info(
                f"[SKIP] Existing Sequence Run Status (sequence_run_id={run_id}, status={status.value})"
            )

        # Due to the disorder of bssh events sequence, we check if the State record is already present
        # rather than checking the latest state
        has_same_state = State.objects.filter(sequence=seq, timestamp=payload.get("dateModified"), status=payload.get("status")).exists()
        if has_same_state:
            logger.info(
                f"[SKIP] Existing Sequence Run State (sequence_run_id={run_id}, status={payload.get('status')})"
            )
        else:
            seq_domain.state_has_changed = True
            logger.info(
                f"Received new Sequence State (sequence_run_id={run_id}, status={payload.get('status')})"
            )

        return seq_domain
