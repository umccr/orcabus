# import django

# django.setup()

# # --- keep ^^^ at top of the module
import uuid
from django.utils.timezone import make_aware
from datetime import datetime
from workflow_manager_proc.domain.executionservice.workflowrunstatechange import WorkflowRunStateChange, Marshaller
from workflow_manager.models.workflow_run import WorkflowRun, Workflow, Payload


def handler(event, context):
    """
    event will be JSON conform to executionservice.WorkflowRunStateChange
    """
    print(f"Processing {event}, {context}")
    
    wrsc: WorkflowRunStateChange = Marshaller.unmarshall(event)

	# We expect: a corresponding Workflow has to exist for each workflow run
    workflow: Workflow = Workflow.objects.get(
        workflow_type = wrsc.workflowName,
        workflow_version = wrsc.workflowVersion
    )

    # first create a new payload entry and assign a unique reference ID for it
    input_payload: Payload = wrsc.payload    
    pld = Payload(
        payload_ref_id = str(uuid.uuid4()),
        version = input_payload.version,
        data = input_payload.data
    )
    pld.save()

    # then create the actual workflow run state change entry
    wfr = WorkflowRun(
        workflow = workflow,
        payload = pld,  # Note: payload type depend on workflow + status and will carry a version in it
        portal_run_id = wrsc.portalRunId,
        execution_id = wrsc.executionId,  # the execution service WRSC does carry the execution ID
        workflow_run_name = wrsc.workflowRunName,
        status = wrsc.status,
        comment = None,
        timestamp = make_aware(wrsc.timestamp)
	)
    wfr.save()

    return wfr  # FIXME: serialise in future (json.dumps)
