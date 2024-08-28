import django

django.setup()

# --- keep ^^^ at top of the module
import workflow_manager_proc.domain.executionservice.workflowrunstatechange as srv
import workflow_manager_proc.domain.workflowmanager.workflowrunstatechange as wfm
from workflow_manager_proc.services import emit_workflow_run_state_change, create_workflow_run_state


def handler(event, context):
    """
    Parameters:
        event: JSON event conform to <executionservice>.WorkflowRunStateChange
        context: ignored for now (only used to conform to Lambda handler conventions)
    Procedure:
        - Unpack AWS event
        - create new State for WorkflowRun if required
        - relay the state change as WorkflowManager WRSC event if applicable
    """
    print(f"Processing {event}, {context}")

    # remove the AWSEvent wrapper from our WRSC event
    input_event: srv.AWSEvent = srv.Marshaller.unmarshall(event, srv.AWSEvent)
    input_wrsc: srv.WorkflowRunStateChange = input_event.detail

    # check state list
    out_wrsc = create_workflow_run_state.handler(srv.Marshaller.marshall(input_wrsc), None)
    if out_wrsc:
        # new state resulted in state transition, we can relay the WRSC
        print("Emitting WRSC.")
        emit_workflow_run_state_change.handler(wfm.Marshaller.marshall(out_wrsc), None)
    else:
        # ignore - state has not been updated
        print(f"WorkflowRun state not updated. No event to emit.")

    print(f"{__name__} done.")
