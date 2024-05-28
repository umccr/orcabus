from django.core.management import BaseCommand
from django.db.models import QuerySet

import json
from libumccr import libjson
from workflow_manager.models import WorkflowRun
from workflow_manager.tests.factories import WorkflowRunFactory, WorkflowFactory,  PayloadFactory

# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Generate mock Workflow data into database for local development and testing"

    def handle(self, *args, **options):
        wf_payload = PayloadFactory()
        wf_workflow = WorkflowFactory()

        wf:WorkflowRun = WorkflowRunFactory(
            workflow_run_name = "MockWorkflowRun",
            payload = wf_payload,
            workflow = wf_workflow
        )

        print(libjson.dumps(wf.to_dict()))
        print("Done")
