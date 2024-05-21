# import django

# django.setup()

# # --- keep ^^^ at top of the module
from django.utils.timezone import make_aware
from datetime import datetime
from workflow_manager_proc.domain.executionservice.workflowrunstatechange import WorkflowRunStateChange, Marshaller
from workflow_manager.models.workflow_run import WorkflowRun, Workflow


def handler(event, context):
    """event will be JSON conform to <any service>.WorkflowRunStateChange
    """
    print(f"Processing {event}, {context}")
    
    wrsc: WorkflowRunStateChange = Marshaller.unmarshall(event)

	# We expect: a corresponding Workflow has to exist for each workflow run
    workflow: Workflow = Workflow.objects.get(
        workflow_type = wrsc.workflowType,
        workflow_version = wrsc.workflowVersion
    )
    
    wfr = WorkflowRun(
        workflow = workflow,
        payload = wrsc.payload,  # Note: payload type depend on workflow + status and will carry a version in it
        portal_run_id = wrsc.portalRunId,
        execution_id = None,  # FIXME: Use service specific WRSC which should include it
        workflow_run_name = wrsc.workflowRunName,  # FIXME: get when WRSC schema is updated
        status = wrsc.status,
        comment = None,
        timestamp = make_aware(wrsc.timestamp)
	)
    wfr.save()

    return wfr  # FIXME: serialise in future (json.dumps)
