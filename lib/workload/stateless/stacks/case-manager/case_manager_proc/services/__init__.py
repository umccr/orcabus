import uuid
from case_manager_proc.domain.executionservice.caserunstatechange import CaseRunStateChange
from case_manager.models import Payload


def create_payload_stub_from_wrsc(wrsc: CaseRunStateChange):
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
