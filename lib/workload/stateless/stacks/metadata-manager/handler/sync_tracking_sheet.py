import django
import os
import logging
import datetime
from libumccr import libjson

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.base')
django.setup()

from proc.service.utils import warn_drop_duplicated_library
from proc.service.tracking_sheet_srv import download_tracking_sheet, sanitize_lab_metadata_df, persist_lab_metadata, \
    drop_incomplete_tracking_sheet_records

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Start processing update from google tracking sheet")
    logger.info(f'event: {libjson.dumps(event)}')

    year: str = str(event.get('year', datetime.date.today().year))
    if isinstance(year, list):
        raise ValueError("Year cannot be an array")

    is_emit_eb_events: bool = event.get('is_emit_eb_events', True)

    tracking_sheet_df = download_tracking_sheet(year)
    sanitize_df = sanitize_lab_metadata_df(tracking_sheet_df)
    duplicate_clean_df = warn_drop_duplicated_library(sanitize_df)
    clean_df = drop_incomplete_tracking_sheet_records(duplicate_clean_df)

    result = persist_lab_metadata(clean_df, year, is_emit_eb_events)

    logger.info(f'persist report: {libjson.dumps(result)}')
    return result


if __name__ == '__main__':
    handler({}, {})
