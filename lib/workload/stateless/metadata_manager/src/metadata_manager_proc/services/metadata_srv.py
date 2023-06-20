import logging
import re

import numpy as np
import pandas as pd
from django.db import transaction
from libumccr import libgdrive, libjson
from libumccr.aws import libssm

from metadata_manager.models.metadata import Metadata

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# SSM Parameter Constant
GDRIVE_SERVICE_ACCOUNT = "/umccr/google/drive/lims_service_account_json"
TRACKING_SHEET_ID = "/umccr/google/drive/tracking_sheet_id"


def download_metadata(year: str) -> pd.DataFrame:
    """Download the full original metadata from which to extract the required information

    :param year: the sheet in the metadata spreadsheet to load
    """
    lab_sheet_id = libssm.get_secret(TRACKING_SHEET_ID)
    account_info = libssm.get_secret(GDRIVE_SERVICE_ACCOUNT)

    return libgdrive.download_sheet(account_info, lab_sheet_id, sheet=year)


@transaction.atomic
def persist_hello_srv():
    hello = Metadata()
    hello.text = "Hallo Welt"
    hello.save()


@transaction.atomic
def get_hello_from_db():
    return Metadata.objects.first()
