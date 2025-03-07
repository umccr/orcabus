import django

django.setup()

# --- keep ^^^ at top of the module
import case_manager_proc.domain.executionservice.caserunstatechange as srv
import case_manager_proc.domain.casemanager.caserunstatechange as case
from case_manager_proc.services import emit_case_run_state_change, create_case_run_state
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Parameters:
        event: JSON event conform to <executionservice>.CaseRunStateChange
        context: ignored for now (only used to conform to Lambda handler conventions)
    Procedure:
        - Unpack AWS event
        - create new State for CaseRun if required
        - relay the state change as CaseManager WRSC event if applicable
    """
    logger.info(f"Processing {event}, {context}")

    # remove the AWSEvent wrapper from our WRSC event
    input_event: srv.AWSEvent = srv.Marshaller.unmarshall(event, srv.AWSEvent)
    input_wrsc: srv.CaseRunStateChange = input_event.detail

    # check state list
    out_wrsc = create_case_run_state.handler(srv.Marshaller.marshall(input_wrsc), None)
    if out_wrsc:
        # new state resulted in state transition, we can relay the WRSC
        logger.info("Emitting WRSC.")
        emit_case_run_state_change.handler(case.Marshaller.marshall(out_wrsc), None)
    else:
        # ignore - state has not been updated
        logger.info(f"CaseRun state not updated. No event to emit.")

    logger.info(f"{__name__} done.")
