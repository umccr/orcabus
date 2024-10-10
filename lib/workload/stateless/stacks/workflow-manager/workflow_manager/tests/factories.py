from enum import Enum
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import factory
from django.utils.timezone import make_aware

from workflow_manager.models import Workflow, WorkflowRun, Payload, Library, State


class TestConstant(Enum):
    workflow_name = "TestWorkflow1"
    payload = {
        "key": "value",
        "foo": uuid.uuid4(),
        "bar": datetime.now().astimezone(ZoneInfo('Australia/Sydney')),
        "sub": {"my": "sub"}
    },
    library = {
        "library_id": "L000001",
        "orcabus_id": "01J5M2J44HFJ9424G7074NKTGN"
    }


class WorkflowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workflow

    workflow_name = "TestWorkflow"
    workflow_version = "1.0"
    execution_engine_pipeline_id = str(uuid.uuid4())
    execution_engine = "ICAv2"


class PayloadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payload

    version = "1.0.0"
    payload_ref_id = str(uuid.uuid4())
    data = TestConstant.payload.value


class WorkflowRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkflowRun

    _uid = str(uuid.uuid4())
    portal_run_id = f"20240130{_uid[:8]}"
    execution_id = _uid
    workflow_run_name = f"TestWorkflowRun{_uid[:8]}"
    comment = "Lorem Ipsum"
    # If required, set later
    workflow = None


class LibraryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Library

    library_id = TestConstant.library.value["library_id"]
    orcabus_id = TestConstant.library.value["orcabus_id"]


class StateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = State

    status = "READY"
    timestamp = make_aware(datetime.now())
    comment = "Comment"
    payload = None
    workflow_run = factory.SubFactory(WorkflowRunFactory)
