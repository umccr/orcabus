from django.core.management import BaseCommand
from django.db.models import QuerySet

from workflow_manager.models import WorkflowRun, Payload
from workflow_manager.tests.factories import WorkflowRunFactory,  PayloadFactory, TestConstant

# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Generate mock Workflow data into database for local development and testing"

    def handle(self, *args, **options):
        WorkflowRunFactory(
            workflow_run_name = "MockWorkflowRun",
            payload = PayloadFactory()
        )

        print("Done")
