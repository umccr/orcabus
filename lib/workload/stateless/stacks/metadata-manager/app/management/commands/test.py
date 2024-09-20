import logging
from django.core.management import BaseCommand
from libumccr import libjson

from app.models import Subject

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Trigger lambda handler for sync tracking sheet locally"

    def handle(self, *args, **options):
        qs = Subject.objects.prefetch_related('library_set').all()

        print(qs.filter(library__library_id='LPRJ240012'))
