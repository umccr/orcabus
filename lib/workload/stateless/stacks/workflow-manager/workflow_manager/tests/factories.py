from enum import Enum
from datetime import datetime, timezone

import factory
from django.utils.timezone import make_aware

from workflow_manager.models.workflow import Workflow
from workflow_manager.models.workflow_run import WorkflowRun
from workflow_manager.models.payload import Payload


class  TestConstantCaseOne(Enum):
    workflow_name = "TestWorkflow"
    workflow_version = "1.0"
    workflow_ref_id = "TWF1.0"
    execution_engine = "ICAv2"
    approval_state = "NATA"

    portal_run_id = "20240130abcdefgh"
    execution_id = "wfr.abcdfgh12345678"
    workflow_run_name = f"{workflow_name}_run1"
    status = "ready"

    payload_reference_id = "payload.ref.123"
    payload_type = "ready_payload"
    payload_data = ""


class WorkflowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workflow

    workflow_name =  TestConstantCaseOne.workflow_name.value
    workflow_version =  TestConstantCaseOne.workflow_version.value
    workflow_ref_id =  TestConstantCaseOne.workflow_ref_id.value
    execution_engine =  TestConstantCaseOne.execution_engine.value
    approval_state =  TestConstantCaseOne.approval_state.value


class PayloadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payload

    payload_type =  TestConstantCaseOne.payload_type.value
    payload_ref_id =  TestConstantCaseOne.payload_reference_id.value
    data = TestConstantCaseOne.payload_data.value


class WorkflowRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkflowRun

    portal_run_id =  TestConstantCaseOne.portal_run_id.value
    execution_id =  TestConstantCaseOne.execution_id.value
    workflow_run_name =  TestConstantCaseOne.workflow_run_name.value
    status =  TestConstantCaseOne.status.value
    comment = "Lorem Ipsum"
    timestamp = make_aware(datetime.now())
    payload = factory.SubFactory(PayloadFactory)
    workflow = factory.SubFactory(WorkflowFactory)


