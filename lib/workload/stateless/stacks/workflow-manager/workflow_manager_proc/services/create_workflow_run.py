# import django

# django.setup()

# # --- keep ^^^ at top of the module
import uuid
from datetime import datetime

from django.db import transaction
from django.utils.timezone import make_aware
from workflow_manager_proc.domain.executionservice.workflowrunstatechange import (
    WorkflowRunStateChange,
    LibraryRecord,
    Marshaller,
)
from workflow_manager.models import (
    WorkflowRun,
    Workflow,
    State,
    Payload,
    Library,
    LibraryAssociation,
)
from . import create_workflow_run_state

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

    # then create the actual workflow run entry if it does not exist
    try:
        wfr: WorkflowRun = WorkflowRun.objects.get(portal_run_id=wrsc.portalRunId)
        wfr.current_status = wrsc.status
        wfr.last_modified = wrsc.timestamp
    except Exception:
        print("No workflow found! Creating new entry.")
        wfr = WorkflowRun(
            workflow=workflow,
            portal_run_id=wrsc.portalRunId,
            execution_id=wrsc.executionId,  # the execution service WRSC does carry the execution ID
            workflow_run_name=wrsc.workflowRunName,
            current_status=wrsc.status,
            comment=None,
            last_modified=wrsc.timestamp,
            created=wrsc.timestamp
        )
    print("Persisting Workflow record.")
    wfr.save()

    # create the related state & payload entries for the WRSC
    create_workflow_run_state(wrsc=wrsc, wfr=wfr)

    # if the workflow run is linked to library record(s), create the association(s)
    input_libraries: list[LibraryRecord] = wrsc.linkedLibraries
    if input_libraries:
        for input_rec in input_libraries:
            # check if the library has already a DB record
            db_lib: Library = Library.objects.get_by_keyword(orcabus_id=input_rec.orcabusId)
            # create it if not
            if not db_lib:
                # TODO: the library record should exist in the future - synced with metadata service on
                #       LibraryStateChange events
                db_lib = Library.objects.create(orcabus_id=input_rec.orcabusId, library_id=input_rec.libraryId)

            # create the library association
            LibraryAssociation.objects.create(
                workflow_run=wfr,
                library=db_lib,
                association_date=make_aware(datetime.now()),
                status=ASSOCIATION_STATUS,
            )

    print(f"{__name__} done.")
    return wfr  # FIXME: serialise in future (json.dumps)
