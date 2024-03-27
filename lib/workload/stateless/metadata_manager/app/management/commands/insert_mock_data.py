from django.core.management import BaseCommand
from django.core import serializers

from app.models import Subject, Specimen, Library
from app.tests.utils import insert_mock_1
from django.core.management import call_command


class Command(BaseCommand):
    help = "Generate mock Metadata into database for local development and testing"

    def handle(self, *args, **options):
        # insert_mock_1()

        sub_o, cre = Subject.objects.get_or_create(
            internal_id="sub01",
            defaults={
                "internal_id": "sub01",
            }
        )

        sub_o2, cre = Subject.objects.update_or_create(
            internal_id="sub02",
            defaults={
                "internal_id": "sub02",
            }
        )

        spec_o, cre = Specimen.objects.get_or_create(
            internal_id="spc1",
            defaults={
                "internal_id": 'spc1'
            }
        )
        spec_o.subjects.add(sub_o2)
        spec_o.subjects.add(sub_o)

        last_record = spec_o.history.latest()

        previous_record = last_record.prev_record
        delta = last_record.diff_against(previous_record)

        for change in delta.changes:
            print("{} changed from {} to {}".format(change.field, change.old, change.new))
        # de = Specimen.objects.get(internal_id="abcd")
        # de.subjects.remove(sub_o)
        # spec_o.subjects.add(sub_o)

        # print('obj', objec)
        # print('cre', cre)
        # print(call_command("clean_duplicate_history", "--auto"))
        print("done")
