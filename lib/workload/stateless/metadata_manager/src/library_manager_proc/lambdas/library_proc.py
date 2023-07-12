from library_manager_proc.services import library_srv
from libumccr import libjson
import os
import django

import logging
from datetime import datetime
from django.utils import timezone

django.setup()


logger = logging.getLogger()
logger.setLevel(logging.INFO)

list_of_years = ["2019", "2020", "2021", "2022", "2023"]


def _halt(msg):
    logger.error(msg)
    return {"message": msg}


def sync_library_from_gdrive(event, context):
    """
    event payload:
    {
        years: ["2019", "2020", "2021", "2022", "2023"],
    }
    """
    logger.info("Start processing LabLibrary update event")
    logger.info(libjson.dumps(event))

    requested_timestamp = datetime.now(tz=timezone.utc)

    timestamp_string = requested_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Reading LabLibrary sheet from google drive at {timestamp_string}")

    # By default it will sync up to the list specified
    years = event.get("sheets", list_of_years)

    if not isinstance(years, list):
        _halt(
            f"Payload error. Must be array of string for sheets. Found: {type(years)}"
        )

    resp_d = {}
    for year in years:
        logger.info(f"Downloading {year} sheet")
        df = library_srv.download_library(year)
        stats_d = library_srv.append_new_library_records(df, requested_timestamp)
        resp_d.update({year: stats_d})

    logger.info(f"Update result from this sync {libjson.dumps(resp_d)}")

    return resp_d
