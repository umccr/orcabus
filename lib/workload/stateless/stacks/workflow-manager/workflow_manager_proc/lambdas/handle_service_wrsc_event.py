import django

django.setup()

# --- keep ^^^ at top of the module
import workflow_manager.aws_event_bridge.executionservice.workflowrunstatechange as srv
import workflow_manager.aws_event_bridge.workflowmanager.workflowrunstatechange as wfm
from workflow_manager_proc.services import emit_workflow_run_state_change, create_workflow_run_state
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
    logger.info(f"Processing {event}, {context}")

    # remove the AWSEvent wrapper from our WRSC event
    input_event: srv.AWSEvent = srv.Marshaller.unmarshall(event, srv.AWSEvent)
    input_wrsc: srv.WorkflowRunStateChange = input_event.detail

    # check state list
    out_wrsc = create_workflow_run_state.handler(srv.Marshaller.marshall(input_wrsc), None)
    if out_wrsc:
        # new state resulted in state transition, we can relay the WRSC
        logger.info("Emitting WRSC.")
        emit_workflow_run_state_change.handler(wfm.Marshaller.marshall(out_wrsc), None)
    else:
        # ignore - state has not been updated
        logger.info(f"WorkflowRun state not updated. No event to emit.")

    logger.info(f"{__name__} done.")
