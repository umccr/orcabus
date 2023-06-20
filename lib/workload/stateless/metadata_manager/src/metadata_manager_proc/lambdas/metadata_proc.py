import os
import django

import logging
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metadata_manager.settings.base")
django.setup()

# --- keep ^^^ at top of the module

from libumccr import libjson

from metadata_manager_proc.services import metadata_srv

logger = logging.getLogger()
logger.setLevel(logging.INFO)

list_of_years = ["2019", "2020", "2021", "2022", "2023"]


def _halt(msg):
    logger.error(msg)
    return {"message": msg}


def update_metadata_from_gdrive(event, context):
    """
    event payload:
    {
        years: ["2019", "2020", "2021", "2022", "2023"],
    }
    """
    logger.info("Start processing LabMetadata update event")
    logger.info(libjson.dumps(event))

    requested_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Reading LabMetadata sheet from google drive at {requested_time}")

    years = event.get("sheets", list_of_years)

    if not isinstance(years, list):
        _halt(
            f"Payload error. Must be array of string for sheets. Found: {type(years)}"
        )

    resp_d = {}
    for year in years:
        logger.info(f"Downloading {year} sheet")
        df = metadata_srv.download_metadata(year)
        stats_d = metadata_srv.persist_labmetadata(df)
        resp_d.update({year: stats_d})

    return resp_d
