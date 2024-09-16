from django.core.management import BaseCommand
from fastq_manager.models import FastqPair


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Delete all DB data"

    def handle(self, *args, **options):
        FastqPair.objects.all().delete()

        print("Done")
