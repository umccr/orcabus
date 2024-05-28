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
    wrsc_matches = get_workflow_run.handler(query, None)  # FIXME: may only need to be a "exist" query
    
    # check workflow run list
    if len(wrsc_matches) == 0:
        # create new entry
        db_wfr: WorkflowRun = create_workflow_run.handler(srv.Marshaller.marshall(input_wrsc), None)
        
		# create outgoing event
        out_event = wfm.WorkflowRunStateChange(
            portalRunId = db_wfr.portal_run_id,
            timestamp = db_wfr.timestamp,
            status = db_wfr.status,
            workflowName = db_wfr.workflow.workflow_name,
            workflowVersion = db_wfr.workflow.workflow_version,
            payload = db_wfr.payload  # the DB payload (as opposed to the input payload) will have a reference ID
		)

        # emit state change
        emit_workflow_run_state_change.handler(wfm.Marshaller.marshall(out_event), None)
    else:
        # ignore - status already exists
        print(f"WorkflowRun already exists for query:{query}")
