import django

django.setup()

# --- keep ^^^ at top of the module
import datetime
from workflow_manager.models import WorkflowRun, State
import workflow_manager_proc.domain.executionservice.workflowrunstatechange as srv
import workflow_manager_proc.domain.workflowmanager.workflowrunstatechange as wfm
from workflow_manager_proc.services import create_workflow_run, emit_workflow_run_state_change, \
    create_workflow_run_state

default_time_window = datetime.timedelta(hours=1)


def handler(event, context):
    """event will be a <any service>.WorkflowRunStateChange event"""
    print(f"Processing {event}, {context}")

    input_event: srv.AWSEvent = srv.Marshaller.unmarshall(event, srv.AWSEvent)
    input_wrsc: srv.WorkflowRunStateChange = input_event.detail

    print(f"Finding WorkflowRun records for portal_run_id:{input_wrsc.portalRunId}")
    try:
        wfr: WorkflowRun = WorkflowRun.objects.get(portal_run_id=input_wrsc.portalRunId)
    except Exception:
        wfr: WorkflowRun = create_workflow_run.handler(srv.Marshaller.marshall(input_wrsc), None)

    state_matches = State.objects.filter(workflow_run=wfr)
    if input_wrsc.status:
        state_matches = state_matches.filter(status=input_wrsc.status)
    if input_wrsc.timestamp:
        dt = datetime.datetime.fromisoformat(str(input_wrsc.timestamp))
        start_t = dt - default_time_window
        end_t = dt + default_time_window
        state_matches = state_matches.filter(timestamp__range=(start_t, end_t))

    # check state list
    if len(state_matches) == 0:
        print(f"No matching WorkflowRun State found. Creating...")
        # create new state entry
        wfr_state: State = create_workflow_run_state(wrsc=input_wrsc, wfr=wfr)

        # create outgoing event
        out_event = map_db_record_to_wrsc(wfr, wfr_state)

        # emit state change
        print("Emitting WRSC.")
        emit_workflow_run_state_change.handler(wfm.Marshaller.marshall(out_event), None)
    else:
        # ignore - status already exists
        print(f"WorkflowRun state already exists. Nothing to do.")

    print(f"{__name__} done.")


def map_db_record_to_wrsc(db_record: WorkflowRun, state: State) -> wfm.WorkflowRunStateChange:
    wrsc = wfm.WorkflowRunStateChange(
        portalRunId=db_record.portal_run_id,
        timestamp=state.timestamp,
        status=state.status,
        workflowName=db_record.workflow.workflow_name,
        workflowVersion=db_record.workflow.workflow_version,
        workflowRunName=db_record.workflow_run_name,
    )

    # handle condition: Payload is optional
    if state.payload:
        wrsc.payload = wfm.Payload(
            refId=state.payload.payload_ref_id,
            version=state.payload.version,
            data=state.payload.data
        )

    return wrsc
