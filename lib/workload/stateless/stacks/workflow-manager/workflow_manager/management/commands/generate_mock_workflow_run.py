from django.core.management import BaseCommand
from django.db.models import QuerySet

from workflow_manager.models import WorkflowRun
from workflow_manager.tests.factories import WorkflowRunFactory,  TestConstantCaseOne

# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Generate mock Workflow data into database for local development and testing"

    def handle(self, *args, **options):
        qs: QuerySet = WorkflowRun.objects.filter(
            workflow_run_name = TestConstantCaseOne.workflow_run_name.value
        )
        if not qs.exists():
            print("Creating new WorkflowRun record...")
            WorkflowRunFactory()

        print("Done")
