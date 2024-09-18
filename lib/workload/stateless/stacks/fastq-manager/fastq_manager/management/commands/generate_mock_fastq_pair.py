import uuid
from django.core.management import BaseCommand
from fastq_manager.tests.factories import FastqPairFactory


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = """
        Generate mock data and populate DB for local testing.
    """

    def handle(self, *args, **options):

        # create a unique ID for every invocation
        _uid = str(uuid.uuid4())
        lib_id = f"Lib.{_uid[:8]}"
        FastqPairFactory(
            rgid=f"library-unique-id-{lib_id}",
            rgsm=f"specimen.id.{_uid}",
            rglb=lib_id,
            read_1_id=f"file.{_uid}_R1",
            read_2_id=f"file.{_uid}_R2"
        )

        print("Done")
