import django

django.setup()

# --- keep ^^^ at top of the module

from workflow_manager_proc.domain.workflowrunstatechange import (
    WorkflowRunStateChange,
    Marshaller,
    AWSEvent
)
from workflow_manager_proc.services import get_workflow_run, create_workflow_run


def handler(event, context):
    """event will be a WorkflowRunStateChange event"""
    print(f"Processing {event}, {context}")
    input_event: AWSEvent = Marshaller.unmarshall(event)
    input_wrsc: WorkflowRunStateChange = input_event.detail

    query = {
        "portal_run_id": input_wrsc.portalRunId,
        "status": input_wrsc.status,
        "timestamp": input_wrsc.timestamp
	}
    wrsc_matches = get_workflow_run.handler(query)
    
    # check workflow run list
    if len(wrsc_matches) == 0:
        # create new entry
        create_workflow_run.handler(Marshaller.marshall(input_wrsc))
        # emit state change
        pass
    else:
        # ignore - status already exists
        pass
    
    

# emit workflow mananger version of the new state - event

