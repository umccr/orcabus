from enum import Enum
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import factory
from django.utils.timezone import make_aware

from workflow_manager.models import Workflow, WorkflowRun, Payload, Library, State, LibraryAssociation


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


class PrimaryTestData():
    WORKFLOW_NAME = "TestWorkflow"

    STATUS_DRAFT = "DRAFT"
    STATUS_START = "READY"
    STATUS_RUNNING = "RUNNING"
    STATUS_END = "SUCCEEDED"
    STATUS_FAIL = "FAILED"
    STATUS_RESOLVED = "RESOLVED"



    def create_primary(self, generic_payload, libraries):
        """
        Case: a primary workflow with two executions linked to 4 libraries
        The first execution failed and led to a repetition that succeeded
        """

        wf = WorkflowFactory(workflow_name=self.WORKFLOW_NAME + "Primary")

        # The first execution (workflow run 1)
        wfr_1: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=self.WORKFLOW_NAME + "PrimaryRun1",
            portal_run_id="1234",
            workflow=wf
        )

        for i, state in enumerate([self.STATUS_DRAFT, self.STATUS_START, self.STATUS_RUNNING, self.STATUS_FAIL]):
            StateFactory(workflow_run=wfr_1, status=state, payload=generic_payload,
                         timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [0, 1, 2, 3]:
            LibraryAssociation.objects.create(
                workflow_run=wfr_1,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )

        # The second execution (workflow run 2)
        wfr_2: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=self.WORKFLOW_NAME + "PrimaryRun2",
            portal_run_id="1235",
            workflow=wf
        )
        for i, state in enumerate([self.STATUS_DRAFT, self.STATUS_START, self.STATUS_RUNNING, self.STATUS_END]):
            StateFactory(workflow_run=wfr_2, status=state, payload=generic_payload,
                         timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [0, 1, 2, 3]:
            LibraryAssociation.objects.create(
                workflow_run=wfr_2,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )

    def setup(self):

        # Common components: payload and libraries
        generic_payload = PayloadFactory()  # Payload content is not important for now
        libraries = [
            LibraryFactory(orcabus_id="01J5M2JFE1JPYV62RYQEG99CP1", library_id="L000001"),
            LibraryFactory(orcabus_id="02J5M2JFE1JPYV62RYQEG99CP2", library_id="L000002"),
            LibraryFactory(orcabus_id="03J5M2JFE1JPYV62RYQEG99CP3", library_id="L000003"),
            LibraryFactory(orcabus_id="04J5M2JFE1JPYV62RYQEG99CP4", library_id="L000004")
        ]

        self.create_primary(generic_payload, libraries)
