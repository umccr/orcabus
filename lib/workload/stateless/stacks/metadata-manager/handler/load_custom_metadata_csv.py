import django
import os
import logging

from libumccr import libjson

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.base')
django.setup()

from proc.service.utils import sanitize_lab_metadata_df, warn_drop_duplicated_library
from proc.service.load_csv_srv import load_metadata_csv, download_csv_to_pandas

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, _context):
    logger.info(f'event: {libjson.dumps(event)}')

    csv_url = event.get('url', None)
    if csv_url is None:
        raise ValueError("URL is required")

    csv_df = download_csv_to_pandas(csv_url)
    sanitize_df = sanitize_lab_metadata_df(csv_df)
    duplicate_clean_df = warn_drop_duplicated_library(sanitize_df)
    result = load_metadata_csv(duplicate_clean_df)

    logger.info(f'persist report: {libjson.dumps(result)}')
    return result


if __name__ == '__main__':
    handler({}, {})
