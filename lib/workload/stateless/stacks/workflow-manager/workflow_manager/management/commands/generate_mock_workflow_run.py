from django.core.management import BaseCommand
from django.db.models import QuerySet
from django.utils.timezone import make_aware

import json
from datetime import datetime
from libumccr import libjson
from workflow_manager.models import Workflow, WorkflowRun, LibraryAssociation, State
from workflow_manager.tests.factories import WorkflowRunFactory, WorkflowFactory, PayloadFactory, LibraryFactory, \
    StateFactory

WORKFLOW_NAME = "TestWorkflow"


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Generate mock Workflow data into database for local development and testing"

    def handle(self, *args, **options):
        qs: QuerySet = Workflow.objects.filter(workflow_name=WORKFLOW_NAME)

        if qs.exists():
            print("Mock data found, Skipping creation.")
            return
        wf = WorkflowFactory(workflow_name=WORKFLOW_NAME)

        wfr: WorkflowRun = WorkflowRunFactory(
            workflow_run_name="MockWorkflowRun",
            portal_run_id="1234",
            workflow=wf
        )

        wf_payload = PayloadFactory()
        StateFactory(
            workflow_run=wfr,
            payload=wf_payload
        )

        library = LibraryFactory()
        LibraryAssociation.objects.create(
            workflow_run=wfr,
            library=library,
            association_date=make_aware(datetime.now()),
            status="ACTIVE",
        )

        wfr2: WorkflowRun = WorkflowRunFactory(
            workflow_run_name="MockWorkflowRun2",
            portal_run_id="1235",
            workflow=wf
        )
        StateFactory(
            workflow_run=wfr2,
            status="RUNNING",
            payload=wf_payload
        )

        library2 = LibraryFactory(orcabus_id="lib.01J5M2JFE1JPYV62RYQEG99CP5", library_id="L000002")
        LibraryAssociation.objects.create(
            workflow_run=wfr2,
            library=library2,
            association_date=make_aware(datetime.now()),
            status="ACTIVE",
        )

        print(libjson.dumps(wf.to_dict()))
        print("Done")
