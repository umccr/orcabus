import django
import os
import logging
import datetime
from libumccr import libjson

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.base')
django.setup()

from proc.service.utils import warn_drop_duplicated_library
from proc.service.tracking_sheet_srv import download_tracking_sheet, sanitize_lab_metadata_df, persist_lab_metadata

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Start processing update from google tracking sheet")
    logger.info(f'event: {libjson.dumps(event)}')

    year: str = str(event.get('year', datetime.date.today().year))
    if isinstance(year, list):
        raise ValueError("Year cannot be an array")

    tracking_sheet_df = download_tracking_sheet(year)
    sanitize_df = sanitize_lab_metadata_df(tracking_sheet_df)
    duplicate_clean_df = warn_drop_duplicated_library(sanitize_df)
    result = persist_lab_metadata(duplicate_clean_df, year)

    logger.info(f'persist report: {libjson.dumps(result)}')
    return result


if __name__ == '__main__':
    handler({}, {})
