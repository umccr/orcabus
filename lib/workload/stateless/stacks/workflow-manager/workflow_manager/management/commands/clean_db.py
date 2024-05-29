from django.core.management import BaseCommand
from django.db.models import QuerySet

from workflow_manager.models import WorkflowRun, Workflow, Payload

# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Delete all DB data"

    def handle(self, *args, **options):
        WorkflowRun.objects.all().delete()
        Payload.objects.all().delete()
        Workflow.objects.all().delete()

        print("Done")
