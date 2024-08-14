# import django

# django.setup()

# # --- keep ^^^ at top of the module
import uuid
from datetime import datetime

from django.db import transaction
from django.utils.timezone import make_aware
from workflow_manager_proc.domain.executionservice.workflowrunstatechange import (
    WorkflowRunStateChange,
    Marshaller,
)
from workflow_manager.models.workflow_run import (
    WorkflowRun,
    Workflow,
    Payload,
    Library,
    LibraryAssociation,
)

ASSOCIATION_STATUS = "ACTIVE"


@transaction.atomic
def handler(event, context):
    """
    event will be JSON conform to executionservice.WorkflowRunStateChange
    """
    print(f"Processing {event}, {context}")

    wrsc: WorkflowRunStateChange = Marshaller.unmarshall(event, WorkflowRunStateChange)
    print(wrsc)

    # We expect: a corresponding Workflow has to exist for each workflow run
    # TODO: decide whether we allow dynamic workflow creation or expect them to exist and fail if not
    try:
        print(f"Looking for workflow ({wrsc.workflowName}:{wrsc.workflowVersion}).")
        workflow: Workflow = Workflow.objects.get(
            workflow_name=wrsc.workflowName, workflow_version=wrsc.workflowVersion
        )
    except Exception:
        print("No workflow found! Creating new entry.")
        workflow = Workflow(
            workflow_name=wrsc.workflowName,
            workflow_version=wrsc.workflowVersion,
            execution_engine="Unknown",
            execution_engine_pipeline_id="Unknown",
            approval_state="RESEARCH",
        )
        print("Persisting Workflow record.")
        workflow.save()

    # then create the actual workflow run state change entry
    wfr = WorkflowRun(
        workflow=workflow,
        portal_run_id=wrsc.portalRunId,
        execution_id=wrsc.executionId,  # the execution service WRSC does carry the execution ID
        workflow_run_name=wrsc.workflowRunName,
        status=wrsc.status,
        comment=None,
        timestamp=wrsc.timestamp,
    )

    # if payload is not null, create a new payload entry and assign a unique reference ID for it
    input_payload: Payload = wrsc.payload
    if input_payload:
        pld = Payload(
            payload_ref_id=str(uuid.uuid4()),
            version=input_payload.version,
            data=input_payload.data,
        )
        print("Persisting Payload record.")
        pld.save()

        wfr.payload = pld  # Note: payload type depend on workflow + status and will carry a version in it

    print("Persisting WorkflowRun record.")
    wfr.save()

    # if the workflow run is linked to library record(s), create the association(s)
    input_libraries: list[str] = wrsc.linkedLibraries
    for input_lib in input_libraries:
        # check if the library has already a DB record
        db_lib: Library = Library.objects.get_by_keyword(library_id=input_lib)
        # create it if not
        if not db_lib:
            db_lib = Library.objects.create(library_id=input_lib)

        # create the library association
        LibraryAssociation.objects.create(
            workflow_run=wfr,
            library=db_lib,
            association_date=make_aware(datetime.now()),
            status=ASSOCIATION_STATUS,
        )

    print(f"{__name__} done.")
    return wfr  # FIXME: serialise in future (json.dumps)
