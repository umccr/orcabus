from django.core.management import BaseCommand
from django.db.models import QuerySet

from sequence_run_manager.models import Sequence
from sequence_run_manager.tests.factories import SequenceFactory, TestConstant


class Command(BaseCommand):
    help = "Generate mock Sequence run data into database for local development and testing"

    def handle(self, *args, **options):
        qs: QuerySet = Sequence.objects.filter(
            sequence_run_id=TestConstant.sequence_run_id.value
        )
        if not qs.exists():
            SequenceFactory()

        print("Done")
