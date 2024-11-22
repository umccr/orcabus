import uuid
from workflow_manager.aws_event_bridge.executionservice.workflowrunstatechange import WorkflowRunStateChange
from workflow_manager.models import Payload


def create_payload_stub_from_wrsc(wrsc: WorkflowRunStateChange):
    # TODO: find better place for this
    input_payload: Payload = wrsc.payload
    if input_payload:
        pld: Payload = Payload(
            payload_ref_id=str(uuid.uuid4()),
            version=input_payload.version,
            data=input_payload.data,
        )
        return pld
    return None
