from django.core.management import BaseCommand
from django.utils.timezone import make_aware

from datetime import datetime, timedelta
from workflow_manager.models import Workflow, WorkflowRun, LibraryAssociation
from workflow_manager.tests.factories import WorkflowRunFactory, WorkflowFactory, PayloadFactory, LibraryFactory, \
    StateFactory

WORKFLOW_NAME = "TestWorkflow"

STATUS_DRAFT = "DRAFT"
STATUS_START = "READY"
STATUS_RUNNING = "RUNNING"
STATUS_END = "SUCCEEDED"
STATUS_FAIL = "FAILED"
STATUS_RESOLVED = "RESOLVED"


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = """
        Generate mock data and populate DB for local testing.
    """

    def handle(self, *args, **options):
        # don't do anything if there is already mock data
        if Workflow.objects.filter(workflow_name__startswith=WORKFLOW_NAME).exists():
            print("Mock data found, Skipping creation.")
            return

        # Common components: payload and libraries
        generic_payload = PayloadFactory()  # Payload content is not important for now
        libraries = [
            LibraryFactory(orcabus_id="01J5M2JFE1JPYV62RYQEG99CP1", library_id="L000001"),
            LibraryFactory(orcabus_id="02J5M2JFE1JPYV62RYQEG99CP2", library_id="L000002"),
            LibraryFactory(orcabus_id="03J5M2JFE1JPYV62RYQEG99CP3", library_id="L000003"),
            LibraryFactory(orcabus_id="04J5M2JFE1JPYV62RYQEG99CP4", library_id="L000004")
        ]

        # First case: a primary workflow with two executions linked to 4 libraries
        # The first execution failed and led to a repetition that succeeded
        self.create_primary(generic_payload, libraries)
        self.create_secondary(generic_payload, libraries)

        print("Done")

    @staticmethod
    def create_primary(generic_payload, libraries):
        """
        Case: a primary workflow with two executions linked to 4 libraries
        The first execution failed and led to a repetition that succeeded
        """

        wf = WorkflowFactory(workflow_name=WORKFLOW_NAME + "Primary")

        # The first execution (workflow run 1)
        wfr_1: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=WORKFLOW_NAME + "PrimaryRun1",
            portal_run_id="1234",
            workflow=wf
        )

        for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_FAIL]):
            StateFactory(workflow_run=wfr_1, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [0, 1, 2, 3]:
            LibraryAssociation.objects.create(
                workflow_run=wfr_1,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )

        # The second execution (workflow run 2)
        wfr_2: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=WORKFLOW_NAME + "PrimaryRun2",
            portal_run_id="1235",
            workflow=wf
        )
        for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_END]):
            StateFactory(workflow_run=wfr_2, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [0, 1, 2, 3]:
            LibraryAssociation.objects.create(
                workflow_run=wfr_2,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )

    @staticmethod
    def create_secondary(generic_payload, libraries):
        """
        Case: a secondary pipeline comprising 3 workflows with corresponding executions
        First workflow: QC (2 runs for 2 libraries)
        Second workflow: Alignment (1 run for 2 libraries)
        Third workflow: VariantCalling (1 run for 2 libraries)
        """

        wf_qc = WorkflowFactory(workflow_name=WORKFLOW_NAME + "QC")

        # QC of Library 1
        wfr_qc_1: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=WORKFLOW_NAME + "QCRunLib1",
            portal_run_id="2345",
            workflow=wf_qc
        )
        for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_END]):
            StateFactory(workflow_run=wfr_qc_1, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        LibraryAssociation.objects.create(
            workflow_run=wfr_qc_1,
            library=libraries[0],
            association_date=make_aware(datetime.now()),
            status="ACTIVE",
        )

        # QC of Library 2
        wfr_qc_2: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=WORKFLOW_NAME + "QCRunLib2",
            portal_run_id="2346",
            workflow=wf_qc
        )
        for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_FAIL, STATUS_RESOLVED]):
            StateFactory(workflow_run=wfr_qc_2, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        LibraryAssociation.objects.create(
            workflow_run=wfr_qc_2,
            library=libraries[1],
            association_date=make_aware(datetime.now()),
            status="ACTIVE",
        )

        # Alignment
        wf_align = WorkflowFactory(workflow_name=WORKFLOW_NAME + "Alignment")
        wfr_a: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=WORKFLOW_NAME + "AlignmentRun",
            portal_run_id="3456",
            workflow=wf_align
        )
        for i, state in enumerate([STATUS_DRAFT, STATUS_START]):
            StateFactory(workflow_run=wfr_a, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [0, 1]:
            LibraryAssociation.objects.create(
                workflow_run=wfr_a,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )

        # Variant Calling
        wf_vc = WorkflowFactory(workflow_name=WORKFLOW_NAME + "VariantCalling")
        wfr_vc: WorkflowRun = WorkflowRunFactory(
            workflow_run_name=WORKFLOW_NAME + "VariantCallingRun",
            portal_run_id="4567",
            workflow=wf_vc
        )
        for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING]):
                StateFactory(workflow_run=wfr_vc, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [0, 1]:
            LibraryAssociation.objects.create(
                workflow_run=wfr_vc,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )
