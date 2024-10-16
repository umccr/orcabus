from django.core.management import BaseCommand

from workflow_manager.models import (
    WorkflowRun,
    Workflow,
    Payload,
    State,
    Library,
    LibraryAssociation,
    Analysis,
    AnalysisRun,
    AnalysisContext
)


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Delete all DB data"

    def handle(self, *args, **options):
        Workflow.objects.all().delete()
        WorkflowRun.objects.all().delete()
        State.objects.all().delete()
        Payload.objects.all().delete()
        Library.objects.all().delete()
        LibraryAssociation.objects.all().delete()
        AnalysisContext.objects.all().delete()
        AnalysisRun.objects.all().delete()
        Analysis.objects.all().delete()

        print("Done")
