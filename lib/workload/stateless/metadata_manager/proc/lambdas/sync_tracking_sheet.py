import logging

from proc.service.tracking_sheet_srv import download_tracking_sheet, sanitize_lab_metadata_df, persist_lab_metadata

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Start processing update from google tracking sheet")

    tracking_sheet_df = download_tracking_sheet()

    sanitize_df = sanitize_lab_metadata_df(tracking_sheet_df)
    result = persist_lab_metadata(sanitize_df)

    return result


if __name__ == '__main__':
    handler({}, {})
