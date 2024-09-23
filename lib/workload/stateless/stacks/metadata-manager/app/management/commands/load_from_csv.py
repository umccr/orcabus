import logging
from django.core.management import BaseCommand
from libumccr import libjson

from handler.load_custom_metadata_csv import handler

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Trigger lambda handler for to sync metadata from csv url"

    def handle(self, *args, **options):
        event = {
            "url": "SOME_URL",
        }

        print(f"Trigger lambda handler for sync tracking sheet. Event {libjson.dumps(event)}")
        result = handler(event, {})

        print(f"result: {libjson.dumps(result)}")
