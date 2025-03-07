from django.core.management import BaseCommand

from case_manager.models import (
    Case,
    CaseData,
    Library,
    State,
)


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Delete all DB data"

    def handle(self, *args, **options):
        Case.objects.all().delete()
        CaseData.objects.all().delete()
        State.objects.all().delete()
        Library.objects.all().delete()

        print("Done")
