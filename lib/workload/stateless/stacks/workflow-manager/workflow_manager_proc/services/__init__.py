import uuid
from workflow_manager_proc.domain.executionservice.workflowrunstatechange import WorkflowRunStateChange
from workflow_manager.models import WorkflowRun, State, Payload


def create_workflow_run_state(wrsc: WorkflowRunStateChange, wfr: WorkflowRun):
    input_payload: Payload = wrsc.payload
    pld = None
    if input_payload:
        pld: Payload = Payload(
            payload_ref_id=str(uuid.uuid4()),
            version=input_payload.version,
            data=input_payload.data,
        )
        print("Persisting Payload record.")
        pld.save()

    # create state for the workflow run
    workflow_state: State = State(
        workflow_run=wfr,
        status=wrsc.status,
        timestamp=wrsc.timestamp,
        comment=None,
        payload=pld
    )
    workflow_state.save()

    return workflow_state
