import logging
import os
from django.core.management import BaseCommand
from libumccr import libjson

from handler.load_custom_metadata_csv import handler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

current_dir = os.path.dirname(__file__)

class Command(BaseCommand):
    help = "Trigger lambda handler for to sync metadata from csv url"

    def handle(self, *args, **options):
        event = {
            "url": os.path.join(current_dir, '../data/mock_sheet.csv'),
            "is_emit_eb_events": False,
            "user_id": "local"
        }

        print(f"Trigger lambda handler for sync tracking sheet. Event {libjson.dumps(event)}")
        result = handler(event, {})

        print(f"result: {libjson.dumps(result)}")
