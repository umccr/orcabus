import logging
from django.core.management import BaseCommand
from libumccr import libjson

from handler.sync_tracking_sheet import handler

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Trigger lambda handler for sync tracking sheet locally"

    def handle(self, *args, **options):
        event = {
            "year": 2024,
            "is_emit_eb_events": False
        }

        print(f"Trigger lambda handler for sync tracking sheet. Event {libjson.dumps(event)}")
        result = handler(event, {})

        print(f"result: {libjson.dumps(result)}")
