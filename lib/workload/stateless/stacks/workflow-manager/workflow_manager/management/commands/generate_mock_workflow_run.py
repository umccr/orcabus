from django.core.management import BaseCommand
from django.db.models import QuerySet
from django.utils.timezone import make_aware

import json
from datetime import datetime
from libumccr import libjson
from workflow_manager.models import WorkflowRun, LibraryAssociation
from workflow_manager.tests.factories import WorkflowRunFactory, WorkflowFactory, PayloadFactory, LibraryFactory


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Generate mock Workflow data into database for local development and testing"

    def handle(self, *args, **options):
        wf_payload = PayloadFactory()
        wf_workflow = WorkflowFactory()

        wf: WorkflowRun = WorkflowRunFactory(
            workflow_run_name="MockWorkflowRun",
            payload=wf_payload,
            workflow=wf_workflow
        )

        library = LibraryFactory()
        LibraryAssociation.objects.create(
            workflow_run=wf,
            library=library,
            association_date=make_aware(datetime.now()),
            status="ACTIVE",
        )

        print(libjson.dumps(wf.to_dict()))
        print("Done")
