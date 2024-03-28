import logging
import datetime
import numpy as np

from proc.service.tracking_sheet_srv import download_tracking_sheet, sanitize_lab_metadata_df, persist_lab_metadata, \
    warn_drop_duplicated_library

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_YEAR = [str(i) for i in np.arange(2017, datetime.date.today().year)]


def handler(event, context):
    logger.info("Start processing update from google tracking sheet")

    year_array = event.get('years', DEFAULT_YEAR)

    tracking_sheet_df = download_tracking_sheet(year_array)

    sanitize_df = sanitize_lab_metadata_df(tracking_sheet_df)
    duplicate_clean_df = warn_drop_duplicated_library(sanitize_df)
    result = persist_lab_metadata(duplicate_clean_df)

    return result


if __name__ == '__main__':
    handler({}, {})
