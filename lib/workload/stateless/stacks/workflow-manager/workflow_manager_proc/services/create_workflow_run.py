# import django

# django.setup()

# # --- keep ^^^ at top of the module
from django.utils.timezone import make_aware
from datetime import datetime
from workflow_manager_proc.domain.workflowrunstatechange import WorkflowRunStateChange, Marshaller
from workflow_manager.models.workflow_run import WorkflowRun


def handler(event, context):
    """event will be JSON conform to WorkflowRunStateChange
    """
    print(f"Processing {event}, {context}")
    
    wrsc: WorkflowRunStateChange = Marshaller.unmarshall(event)

    # workflow = Workflow.objects.filter(
    #     workflow_type = "",
    #     workflow_version = ""
    # )

    wfr = WorkflowRun(
        workflow = None,  # FIXME: lookup workflow based on Workflow type and version
        payload = wrsc.payload,  # Note: payload type depend on workflow + status and will carry a version in it
        portal_run_id = wrsc.portalRunId,
        execution_id = None,   # FIXME: Optional, use for e.g. UI to lookup execution engine details for this run (ICA API analysis-id)
        workflow_run_name = None,  # FIXME: decide what to use and where to get it from
        status = wrsc.status,
        comment = None,
        timestamp = make_aware(wrsc.timestamp)
	)
    wfr.save()

    return wfr  # FIXME: serialise in future (json.dumps)
