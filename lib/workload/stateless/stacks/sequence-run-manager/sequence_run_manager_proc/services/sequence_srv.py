import logging

from django.db import transaction
from django.db.models import QuerySet

from sequence_run_manager.models.sequence import Sequence, SequenceStatus
from sequence_run_manager.models.state import State
from sequence_run_manager_proc.domain.sequence import SequenceDomain
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
    instrument_run_id = payload["instrumentRunId"]
    gds_folder_path = payload["gdsFolderPath"]
    gds_volume_name = payload["gdsVolumeName"]
    date_modified = payload["dateModified"]
    
    # key to retrieve further details of icav2 bssh event
    ica_project_id = payload.get("icaProjectId")
    api_url = payload.get("apiUrl")
    v1pre3_id = payload.get("v1pre3Id")
    
    # optional
    run_id = payload.get("id")
    name = payload.get("name")
    sample_sheet_name = payload.get("sampleSheetName")
    reagent_barcode = payload.get("reagentBarcode")
    flowcell_barcode = payload.get("flowcellBarcode")
    
    # --- start mapping to internal Sequence model

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
    qs: QuerySet = Sequence.objects.filter(instrument_run_id=instrument_run_id)

    if not qs.exists():
        logger.info(f"Creating new Sequence (instrument_run_id={instrument_run_id})")

        seq = Sequence()

        seq.instrument_run_id = instrument_run_id
        seq.run_volume_name = gds_volume_name
        seq.run_folder_path = gds_folder_path
        seq.run_data_uri = f"{GDS_URI_SCHEME}{gds_volume_name}{gds_folder_path}"
        seq.status = status
        seq.start_time = start_time
        seq.end_time = end_time

        seq.reagent_barcode = reagent_barcode
        seq.flowcell_barcode = flowcell_barcode
        seq.sample_sheet_name = sample_sheet_name
        seq.sequence_run_id = run_id
        seq.sequence_run_name = name
        
        seq.v1pre3_id = v1pre3_id
        seq.ica_project_id = ica_project_id
        seq.api_url = api_url
        
        # get run details from bssh srv api call
        bssh_service = BSSHService()
        run_details = bssh_service.get_run_details(api_url)
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
            f"Created new Sequence (instrument_run_id={instrument_run_id}, status={status.value})"
        )
        return SequenceDomain(sequence=seq, status_has_changed=True, state_has_changed=True)
    else:
        seq: Sequence = qs.get()
        seq_domain = SequenceDomain(sequence=seq)

        if seq.status != status.value:
            logger.info(
                f"Updating Sequence (instrument_run_id={instrument_run_id}, status={status.value})"
            )
            seq.status = status
            seq.end_time = end_time
            seq.save()
            logger.info(
                f"Updated Sequence (instrument_run_id={instrument_run_id}, status={status.value})"
            )
            seq_domain.status_has_changed = True
        else:
            logger.info(
                f"[SKIP] Existing Sequence Run Status (instrument_run_id={instrument_run_id}, status={status.value})"
            )

        # Due to the chaos of bssh events sequence from event sqs, we check if the State record is already present
        # rather than checking the latest state
        isExistSameState = State.objects.filter(sequence=seq, timestamp=payload["dateModified"], status=payload["status"]).exists()
        if isExistSameState:
            logger.info(
                f"[SKIP] Existing Sequence Run State (instrument_run_id={instrument_run_id}, status={payload['status']})"
            )
        else:
            seq_domain.state_has_changed = True
            logger.info(
                f"Received new Sequence State (instrument_run_id={instrument_run_id}, status={payload['status']})"
            )

        return seq_domain
