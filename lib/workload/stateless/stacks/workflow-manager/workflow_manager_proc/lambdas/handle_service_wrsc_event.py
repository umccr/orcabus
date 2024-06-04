import django

django.setup()

# --- keep ^^^ at top of the module
import json
from  enum import Enum
from deepdiff import DeepDiff
from datetime import datetime
from workflow_manager.models.workflow_run import WorkflowRun
from workflow_manager.models.payload import Payload
import workflow_manager_proc.domain.executionservice.workflowrunstatechange as srv
import workflow_manager_proc.domain.workflowmanager.workflowrunstatechange as wfm
from workflow_manager_proc.services import get_workflow_run, create_workflow_run, emit_workflow_run_state_change

class Status(Enum):
    RUNNING = 'RUNNING'
    DRAFT = 'DRAFT'

def handler(event, context):
    """event will be a <any service>.WorkflowRunStateChange event"""
    print(f"Processing {event}, {context}")

    input_event: srv.AWSEvent = srv.Marshaller.unmarshall(event, srv.AWSEvent)
    input_wrsc: srv.WorkflowRunStateChange = input_event.detail

    event_status = str(input_wrsc.status).upper()

    query = {
        "portal_run_id": input_wrsc.portalRunId,
        "status": event_status,
    }

    # For RUNNING status we allow updates unless within a certain time window
    if event_status == Status.RUNNING.value:
        query.update(timestamp = input_wrsc.timestamp)


    # For 'DRAFT' status allow new payload records if the payload has changed

    # For all other states, don't allow updates => error / ignore events

    print(f"Finding WorkflowRun records for query:{query}")
    wrsc_matches = get_workflow_run.handler(query, None)  # FIXME: may only need to be a "exist" query

    # check workflow run list
    if len(wrsc_matches) == 0:
        print(f"No matching WorkflowRun found. Creating...")
        # create new entry
        persist_and_publish(input_wrsc)
    else:
        if event_status == Status.DRAFT.value:
            # get the the most recent payload from the DB
            db_workflow = get_latest_workflowrun(wrsc_matches)
            # compare against input event payload
            p1 = input_wrsc.payload
            p2 = db_workflow.payload
            if payload_differs(p1, p2):
                # then create new record
                persist_and_publish(input_wrsc)
            else:
                print(f"{Status.DRAFT.value} WorkflowRun with this payload already exists. Ignoring.")
        else:    
            # FIXME: ignore, or error?
            # We don't expect 
            print(f"WorkflowRun already exists. Nothing to do.")

        # ignore - status already exists
        print(f"WorkflowRun already exists. Nothing to do.")

    print(f"{__name__} done.")


def map_db_record_to_wrsc(db_record: WorkflowRun) -> wfm.WorkflowRunStateChange:
    wrsc = wfm.WorkflowRunStateChange(
        portalRunId=db_record.portal_run_id,
        timestamp=db_record.timestamp,
        status=db_record.status,
        workflowName=db_record.workflow.workflow_name,
        workflowVersion=db_record.workflow.workflow_version,
        workflowRunName=db_record.workflow_run_name,
        payload=wfm.Payload(
            refId=db_record.payload.payload_ref_id,
            version=db_record.payload.version,
            data=db_record.payload.data
        )
    )
    return wrsc


def get_latest_workflowrun(workflowruns: list[WorkflowRun]):
    x_time = 0
    latest_w = None

    for w in workflowruns:
        w_time = w.timestamp.timestamp()
        if w_time > x_time:
            x_time = w_time
            latest_w = w

    return latest_w


def payload_differs(p1, p2) -> bool:
    print(f"Checking payload difference...")
    # Note: DeepDiff takes object 'type' into account, so we strip it down to dict
    d1 = get_payload_data_dict(p1)
    d2 = get_payload_data_dict(p2)
    print(f"Payload 1: {d1}")
    print(f"Payload 2: {d2}")
    # TODO: test for multiple scenarios
    res = DeepDiff(d1, d2, ignore_order=True)
    print("Payload difference:")
    print(res)

    if res:
        print(f"Payloads differ: {res}")
        return True
    else:
        print(f"Payloads don't differ.")
        return False


def persist_and_publish(input_wrsc: srv.WorkflowRunStateChange):
    db_wfr: WorkflowRun = create_workflow_run.handler(srv.Marshaller.marshall(input_wrsc), None)
    out_event = map_db_record_to_wrsc(db_wfr)
    print("Emitting WRSC.")
    print(wfm.Marshaller.marshall(out_event))
    # emit_workflow_run_state_change.handler(wfm.Marshaller.marshall(out_event), None)


def get_payload_data_dict(payload):
    d = payload.data
    if isinstance(d, dict):
        return d
    elif isinstance(d, str):
        return json.loads(d)
    else:
        raise ValueError(f"Payload data {d} of type {type(d)} not supported. Should be JSON string or dict.")
