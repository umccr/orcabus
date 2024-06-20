import django
import os
import logging
import datetime
from libumccr import libjson

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.base')
django.setup()

from proc.service.tracking_sheet_srv import download_tracking_sheet, sanitize_lab_metadata_df, persist_lab_metadata, \
    warn_drop_duplicated_library

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Start processing update from google tracking sheet")
    logger.info(f'event: {libjson.dumps(event)}')

    year_array = event.get('years', [datetime.date.today().year])

    tracking_sheet_df = download_tracking_sheet(year_array)
    sanitize_df = sanitize_lab_metadata_df(tracking_sheet_df)
    duplicate_clean_df = warn_drop_duplicated_library(sanitize_df)
    result = persist_lab_metadata(duplicate_clean_df)

    logger.info(f'persist report: {libjson.dumps(result)}')
    return result


if __name__ == '__main__':
    handler({}, {})
