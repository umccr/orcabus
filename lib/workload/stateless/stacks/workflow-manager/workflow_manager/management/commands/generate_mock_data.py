from django.core.management import BaseCommand
from django.db.models import QuerySet

from workflow_manager.models import Workflow
from workflow_manager.tests.factories import WorkflowFactory, TestConstant


class Command(BaseCommand):
    help = "Generate mock Workflow data into database for local development and testing"

    def handle(self, *args, **options):
        qs: QuerySet = Workflow.objects.filter(
            text=TestConstant.workflow_name.value
        )
        if not qs.exists():
            WorkflowFactory()

        print("Done")
