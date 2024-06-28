import django

django.setup()

# --- keep ^^^ at top of the module
from workflow_manager.models.workflow_run import WorkflowRun
import workflow_manager_proc.domain.executionservice.workflowrunstatechange as srv
import workflow_manager_proc.domain.workflowmanager.workflowrunstatechange as wfm
from workflow_manager_proc.services import get_workflow_run, create_workflow_run, emit_workflow_run_state_change


def handler(event, context):
    """event will be a <any service>.WorkflowRunStateChange event"""
    print(f"Processing {event}, {context}")

    input_event: srv.AWSEvent = srv.Marshaller.unmarshall(event, srv.AWSEvent)
    input_wrsc: srv.WorkflowRunStateChange = input_event.detail

    query = {
        "portal_run_id": input_wrsc.portalRunId,
        "status": input_wrsc.status,
        "timestamp": input_wrsc.timestamp
    }
    print(f"Finding WorkflowRun records for query:{query}")
    wrsc_matches = get_workflow_run.handler(query, None)  # FIXME: may only need to be a "exist" query

    # check workflow run list
    if len(wrsc_matches) == 0:
        print(f"No matching WorkflowRun found. Creating...")
        # create new entry
        db_wfr: WorkflowRun = create_workflow_run.handler(srv.Marshaller.marshall(input_wrsc), None)

        # create outgoing event
        out_event = map_db_record_to_wrsc(db_wfr)

        # emit state change
        print("Emitting WRSC.")
        emit_workflow_run_state_change.handler(wfm.Marshaller.marshall(out_event), None)
    else:
        # ignore - status already exists
        print(f"WorkflowRun already exists. Nothing to do.")

    print(f"{__name__} done.")


def map_db_record_to_wrsc(db_record: WorkflowRun) -> wfm.WorkflowRunStateChange:
    wrsc = wfm.WorkflowRunStateChange(
        portalRunId=db_record.portal_run_id,
        timestamp=db_record.timestamp,
        status=db_record.status,
        workflowName=db_record.workflow.workflow_name,
        workflowVersion=db_record.workflow.workflow_version,
        workflowRunName=db_record.workflow_run_name,
    )

    # handle condition: Payload is optional
    if db_record.payload:
        wrsc.payload = wfm.Payload(
            refId=db_record.payload.payload_ref_id,
            version=db_record.payload.version,
            data=db_record.payload.data
        )

    return wrsc
