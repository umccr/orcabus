# import django

# django.setup()

# # --- keep ^^^ at top of the module
import datetime
import logging

from django.db import transaction
import workflow_manager.aws_event_bridge.executionservice.workflowrunstatechange as srv
import workflow_manager.aws_event_bridge.workflowmanager.workflowrunstatechange as wfm
from workflow_manager.models import (
    WorkflowRun,
    Workflow,
    Library,
    LibraryAssociation,
    State,
    Status,
)
from workflow_manager.models.utils import WorkflowRunUtil
from . import create_payload_stub_from_wrsc

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ASSOCIATION_STATUS = "ACTIVE"


def sanitize_orcabus_id(orcabus_id: str) -> str:
    # TODO: better sanitization and better location
    return orcabus_id[-26:]


@transaction.atomic
def handler(event, context):
    """
    Parameters:
        event: JSON event conform to <executionservice>.WorkflowRunStateChange
        context: ignored for now (only used to conform to Lambda handler conventions)
    Procedure:
        - check whether a corresponding Workflow record exists (it should according to the pre-planning approach)
            - if not exist, create (support on-the-fly approach)
        - check whether a WorkflowRun record exists (it should if this is not the first/initial state)
            - if not exist, create
            - associate any libraries at this point (later updates/linking is not supported at this point)
        - check whether the state change event constitutes a new state
            - the DRAFT state allows payload updates, until it enters the READY state
            - the RUNNING state allows "infrequent" updates (i.e. that happen outside a certain time window)
            - other states will ignore updates of the same state
            - if we have new state, then persist it
            NOTE: all events that don't change any state value should be ignored
    """
    logger.info(f"Start processing {event}, {context}...")
    srv_wrsc: srv.WorkflowRunStateChange = srv.Marshaller.unmarshall(event, srv.WorkflowRunStateChange)

    # We expect: a corresponding Workflow has to exist for each workflow run
    # NOTE: for now we allow dynamic workflow creation
    # TODO: expect workflows to be pre-registered
    # TODO: could move that logic to caller and expect WF to exist here
    try:
        logger.info(f"Looking for Workflow ({srv_wrsc.workflowName}:{srv_wrsc.workflowVersion}).")
        workflow: Workflow = Workflow.objects.get(
            workflow_name=srv_wrsc.workflowName, workflow_version=srv_wrsc.workflowVersion
        )
    except Exception:
        logger.warning("No Workflow record found! Creating new entry.")
        workflow = Workflow(
            workflow_name=srv_wrsc.workflowName,
            workflow_version=srv_wrsc.workflowVersion,
            execution_engine="Unknown",
            execution_engine_pipeline_id="Unknown",
        )
        logger.info("Persisting Workflow record.")
        workflow.save()

    # then create the actual workflow run entry if it does not exist
    try:
        wfr: WorkflowRun = WorkflowRun.objects.get(portal_run_id=srv_wrsc.portalRunId)
    except Exception:
        logger.info("No WorkflowRun record found! Creating new entry.")
        # NOTE: the library linking is expected to be established at workflow run creation time.
        #       Later changes will currently be ignored.
        wfr = WorkflowRun(
            workflow=workflow,
            portal_run_id=srv_wrsc.portalRunId,
            execution_id=srv_wrsc.executionId,  # the execution service WRSC does carry the execution ID
            workflow_run_name=srv_wrsc.workflowRunName,
            comment=None
        )
        logger.info(wfr)
        logger.info("Persisting WorkflowRun record.")
        wfr.save()

        # if the workflow run is linked to library record(s), create the association(s)
        input_libraries: list[srv.LibraryRecord] = srv_wrsc.linkedLibraries
        if input_libraries:
            for input_rec in input_libraries:
                # make sure OrcaBus ID format is sanitized (without prefix) for lookups
                orca_id = sanitize_orcabus_id(input_rec.orcabusId)
                # get the DB record of the library
                try:
                    db_lib: Library = Library.objects.get(orcabus_id=orca_id)
                except Library.DoesNotExist:
                    # The library record should exist - synced with metadata service on LibraryStateChange events
                    # However, until that sync is in place we may need to create a record on demand
                    # FIXME: remove this once library records are automatically synced
                    db_lib = Library.objects.create(orcabus_id=orca_id, library_id=input_rec.libraryId)

                # create the library association
                LibraryAssociation.objects.create(
                    workflow_run=wfr,
                    library=db_lib,
                    association_date=datetime.datetime.now(),
                    status=ASSOCIATION_STATUS,
                )

    wfr_util = WorkflowRunUtil(wfr)

    # Create a new State sub (not persisted)
    new_state = State(
        status=srv_wrsc.status,
        timestamp=srv_wrsc.timestamp,
    )
    if srv_wrsc.payload:
        # handle the payload
        new_state.payload = create_payload_stub_from_wrsc(srv_wrsc)

    # attempt to transition to new state (will persist new state if successful)
    success = wfr_util.transition_to(new_state)
    if not success:
        logger.warning(f"Could not apply new state: {new_state}")
        return None

    wfm_wrsc = map_srv_wrsc_to_wfm_wrsc(srv_wrsc, new_state)

    logger.info(f"{__name__} done.")
    return wfm_wrsc


def map_srv_wrsc_to_wfm_wrsc(input_wrsc: srv.WorkflowRunStateChange, new_state: State) -> wfm.WorkflowRunStateChange:
    out_wrsc = wfm.WorkflowRunStateChange(
        portalRunId=input_wrsc.portalRunId,
        timestamp=input_wrsc.timestamp,
        status=Status.get_convention(input_wrsc.status),  # ensure we follow conventions
        workflowName=input_wrsc.workflowName,
        workflowVersion=input_wrsc.workflowVersion,
        workflowRunName=input_wrsc.workflowRunName,
        linkedLibraries=input_wrsc.linkedLibraries,
    )
    # NOTE: the srv payload is not quite the same as the wfm payload (it's missing a payload ref id that's assigned by the wfm)
    # So, if the new state has a payload, we need to map the service payload to the wfm payload
    if new_state.payload:
        out_wrsc.payload = map_srv_payload_to_wfm_payload(input_wrsc.payload, new_state.payload.payload_ref_id)
    return out_wrsc


def map_srv_payload_to_wfm_payload(input_payload: srv.Payload, ref_id: str) -> wfm.Payload:
    out_payload = wfm.Payload(
        refId=ref_id,
        version=input_payload.version,
        data=input_payload.data
    )
    return out_payload
