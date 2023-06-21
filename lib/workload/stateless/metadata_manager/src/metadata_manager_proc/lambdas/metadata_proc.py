import os
import django

import logging
from datetime import datetime
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metadata_manager.settings.base")
django.setup()


from libumccr import libjson

from metadata_manager_proc.services import metadata_srv

logger = logging.getLogger()
logger.setLevel(logging.INFO)

list_of_years = ["2019", "2020", "2021", "2022", "2023"]


def _halt(msg):
    logger.error(msg)
    return {"message": msg}


def sync_metadata_from_gdrive(event, context):
    """
    event payload:
    {
        years: ["2019", "2020", "2021", "2022", "2023"],
    }
    """
    logger.info("Start processing LabMetadata update event")
    logger.info(libjson.dumps(event))

    requested_timestamp = datetime.now(tz=timezone.utc)

    timestamp_string = requested_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Reading LabMetadata sheet from google drive at {timestamp_string}")

    # By default it will sync up to the list specified
    years = event.get("sheets", list_of_years)

    if not isinstance(years, list):
        _halt(
            f"Payload error. Must be array of string for sheets. Found: {type(years)}"
        )

    resp_d = {}
    for year in years:
        logger.info(f"Downloading {year} sheet")
        df = metadata_srv.download_metadata(year)
        stats_d = metadata_srv.append_new_metadata_records(df, requested_timestamp)
        resp_d.update({year: stats_d})

    logger.info(f"Update result from this sync {libjson.dumps(resp_d)}")

    return resp_d
