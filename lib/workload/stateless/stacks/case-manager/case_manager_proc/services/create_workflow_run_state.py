# import django

# django.setup()

# # --- keep ^^^ at top of the module
import datetime
import logging

from django.db import transaction
import case_manager_proc.domain.executionservice.caserunstatechange as srv
import case_manager_proc.domain.casemanager.caserunstatechange as case
from case_manager.models import (
    CaseRun,
    Case,
    Library,
    LibraryAssociation,
    State,
    Status,
)
from case_manager.models.utils import CaseRunUtil
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
        event: JSON event conform to <executionservice>.CaseRunStateChange
        context: ignored for now (only used to conform to Lambda handler conventions)
    Procedure:
        - check whether a corresponding Case record exists (it should according to the pre-planning approach)
            - if not exist, create (support on-the-fly approach)
        - check whether a CaseRun record exists (it should if this is not the first/initial state)
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
    srv_wrsc: srv.CaseRunStateChange = srv.Marshaller.unmarshall(event, srv.CaseRunStateChange)

    # We expect: a corresponding Case has to exist for each case run
    # NOTE: for now we allow dynamic case creation
    # TODO: expect cases to be pre-registered
    # TODO: could move that logic to caller and expect WF to exist here
    try:
        logger.info(f"Looking for Case ({srv_wrsc.caseName}:{srv_wrsc.caseVersion}).")
        case: Case = Case.objects.get(
            case_name=srv_wrsc.caseName, case_version=srv_wrsc.caseVersion
        )
    except Exception:
        logger.warning("No Case record found! Creating new entry.")
        case = Case(
            case_name=srv_wrsc.caseName,
            case_version=srv_wrsc.caseVersion,
            execution_engine="Unknown",
            execution_engine_pipeline_id="Unknown",
        )
        logger.info("Persisting Case record.")
        case.save()

    # then create the actual case run entry if it does not exist
    try:
        wfr: CaseRun = CaseRun.objects.get(portal_run_id=srv_wrsc.portalRunId)
    except Exception:
        logger.info("No CaseRun record found! Creating new entry.")
        # NOTE: the library linking is expected to be established at case run creation time.
        #       Later changes will currently be ignored.
        wfr = CaseRun(
            case=case,
            portal_run_id=srv_wrsc.portalRunId,
            execution_id=srv_wrsc.executionId,  # the execution service WRSC does carry the execution ID
            case_run_name=srv_wrsc.caseRunName,
            comment=None
        )
        logger.info(wfr)
        logger.info("Persisting CaseRun record.")
        wfr.save()

        # if the case run is linked to library record(s), create the association(s)
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
                    case_run=wfr,
                    library=db_lib,
                    association_date=datetime.datetime.now(),
                    status=ASSOCIATION_STATUS,
                )

    wfr_util = CaseRunUtil(wfr)

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

    case_wrsc = map_srv_wrsc_to_case_wrsc(srv_wrsc, new_state)

    logger.info(f"{__name__} done.")
    return case_wrsc


def map_srv_wrsc_to_case_wrsc(input_wrsc: srv.CaseRunStateChange, new_state: State) -> case.CaseRunStateChange:
    out_wrsc = case.CaseRunStateChange(
        portalRunId=input_wrsc.portalRunId,
        timestamp=input_wrsc.timestamp,
        status=Status.get_convention(input_wrsc.status),  # ensure we follow conventions
        caseName=input_wrsc.caseName,
        caseVersion=input_wrsc.caseVersion,
        caseRunName=input_wrsc.caseRunName,
        linkedLibraries=input_wrsc.linkedLibraries,
    )
    # NOTE: the srv payload is not quite the same as the case payload (it's missing a payload ref id that's assigned by the case)
    # So, if the new state has a payload, we need to map the service payload to the case payload
    if new_state.payload:
        out_wrsc.payload = map_srv_payload_to_case_payload(input_wrsc.payload, new_state.payload.payload_ref_id)
    return out_wrsc


def map_srv_payload_to_case_payload(input_payload: srv.Payload, ref_id: str) -> case.Payload:
    out_payload = case.Payload(
        refId=ref_id,
        version=input_payload.version,
        data=input_payload.data
    )
    return out_payload
