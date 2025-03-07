from django.core.management import BaseCommand
from django.utils.timezone import make_aware

from datetime import datetime, timedelta
from case_manager.models import Case, CaseData, LibraryAssociation
from case_manager.tests.factories import CaseFactory, CaseDataFactory, LibraryFactory, StateFactory

CASE_NAME = "TestCase"

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
        if Case.objects.filter(case_name__startswith=CASE_NAME).exists():
            print("Mock data found, Skipping creation.")
            return

        # Common components: payload and libraries
        # generic_payload = PayloadFactory()  # Payload content is not important for now
        libraries = [
            LibraryFactory(orcabus_id="01J5M2JFE1JPYV62RYQEG99CP1", library_id="L000001"),
            LibraryFactory(orcabus_id="02J5M2JFE1JPYV62RYQEG99CP2", library_id="L000002"),
            LibraryFactory(orcabus_id="03J5M2JFE1JPYV62RYQEG99CP3", library_id="L000011"),
            LibraryFactory(orcabus_id="04J5M2JFE1JPYV62RYQEG99CP4", library_id="L000012")
        ]

        # First case: a primary case with two executions linked to 4 libraries
        # The first execution failed and led to a repetition that succeeded
        self.create_cases(libraries)

        print("Done")

    @staticmethod
    def create_cases(generic_payload, libraries):
        """
        Case: a primary case with two executions linked to 4 libraries
        The first execution failed and led to a repetition that succeeded
        """

        # Test Case 1 with Lib 1/2
        case_1 = CaseFactory(
            case_name=CASE_NAME + "First",
            data = CaseDataFactory(
                cref = "Curation Case 1"
            )
        )
        for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_FAIL]):
            StateFactory(case=case_1, status=state, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [0, 1]:
            LibraryAssociation.objects.create(
                case=case_1,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )

        # Test Case 2 with Lib 11/12
        case_2 = CaseFactory(
            case_name=CASE_NAME + "Second",
            data = CaseDataFactory(
                cref = "Curation Case 2"
            )
        )
        for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_END]):
            StateFactory(case=case_2, status=state, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
        for i in [2, 3]:
            LibraryAssociation.objects.create(
                case=case_2,
                library=libraries[i],
                association_date=make_aware(datetime.now()),
                status="ACTIVE",
            )

    # @staticmethod
    # def create_secondary(generic_payload, libraries):
    #     """
    #     Case: a secondary pipeline comprising 3 cases with corresponding executions
    #     First case: QC (2 runs for 2 libraries)
    #     Second case: Alignment (1 run for 2 libraries)
    #     Third case: VariantCalling (1 run for 2 libraries)
    #     """
    #
    #     wf_qc = CaseFactory(case_name=CASE_NAME + "QC")
    #
    #     # QC of Library 1
    #     wfr_qc_1: CaseRun = CaseRunFactory(
    #         case_run_name=CASE_NAME + "QCRunLib1",
    #         portal_run_id="2345",
    #         case=wf_qc
    #     )
    #     for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_END]):
    #         StateFactory(case_run=wfr_qc_1, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
    #     LibraryAssociation.objects.create(
    #         case_run=wfr_qc_1,
    #         library=libraries[0],
    #         association_date=make_aware(datetime.now()),
    #         status="ACTIVE",
    #     )
    #
    #     # QC of Library 2
    #     wfr_qc_2: CaseRun = CaseRunFactory(
    #         case_run_name=CASE_NAME + "QCRunLib2",
    #         portal_run_id="2346",
    #         case=wf_qc
    #     )
    #     for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING, STATUS_FAIL, STATUS_RESOLVED]):
    #         StateFactory(case_run=wfr_qc_2, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
    #     LibraryAssociation.objects.create(
    #         case_run=wfr_qc_2,
    #         library=libraries[1],
    #         association_date=make_aware(datetime.now()),
    #         status="ACTIVE",
    #     )
    #
    #     # Alignment
    #     wf_align = CaseFactory(case_name=CASE_NAME + "Alignment")
    #     wfr_a: CaseRun = CaseRunFactory(
    #         case_run_name=CASE_NAME + "AlignmentRun",
    #         portal_run_id="3456",
    #         case=wf_align
    #     )
    #     for i, state in enumerate([STATUS_DRAFT, STATUS_START]):
    #         StateFactory(case_run=wfr_a, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
    #     for i in [0, 1]:
    #         LibraryAssociation.objects.create(
    #             case_run=wfr_a,
    #             library=libraries[i],
    #             association_date=make_aware(datetime.now()),
    #             status="ACTIVE",
    #         )
    #
    #     # Variant Calling
    #     wf_vc = CaseFactory(case_name=CASE_NAME + "VariantCalling")
    #     wfr_vc: CaseRun = CaseRunFactory(
    #         case_run_name=CASE_NAME + "VariantCallingRun",
    #         portal_run_id="4567",
    #         case=wf_vc
    #     )
    #     for i, state in enumerate([STATUS_DRAFT, STATUS_START, STATUS_RUNNING]):
    #             StateFactory(case_run=wfr_vc, status=state, payload=generic_payload, timestamp=make_aware(datetime.now() + timedelta(hours=i)))
    #     for i in [0, 1]:
    #         LibraryAssociation.objects.create(
    #             case_run=wfr_vc,
    #             library=libraries[i],
    #             association_date=make_aware(datetime.now()),
    #             status="ACTIVE",
    #         )
