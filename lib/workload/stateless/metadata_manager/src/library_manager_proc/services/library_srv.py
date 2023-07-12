import logging
import re
from datetime import datetime

import numpy as np
import pandas as pd
from django.db import transaction
from libumccr import libgdrive, libjson
from libumccr.aws import libssm

from library_manager.models.library import Library

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# SSM Parameter Constant for accessing Gdrive
GDRIVE_SERVICE_ACCOUNT = "/umccr/google/drive/lims_service_account_json"
TRACKING_SHEET_ID = "/umccr/google/drive/tracking_sheet_id"


@transaction.atomic
def append_new_library_records(df: pd.DataFrame, df_timestamp: datetime):
    """
    Append new library from a pandas DataFrame into the db

    The function will check if the latest library record is up to the with the current df,
    if record is missing or different it will append a new record to the current database.

    :param df: DataFrame to persist
    :param df_timestamp: The timestamp where the DF is fetched
    :return: result statistics - count of LabLibrary rows created
    """

    if df.empty:
        return {"message": "Empty data frame"}

    df = clean_columns(df)
    df = df.applymap(_clean_data_cell)
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    rows_created = list()
    rows_invalid = list()

    for record in df.to_dict("records"):
        library_id = record.get("library_id") or None
        try:
            df_object = {
                "library_id": library_id,
                "sample_name": record.get("sample_name") or None,
                "sample_id": record.get("sample_id") or None,
                "external_sample_id": record["external_sample_id"],
                "subject_id": record["subject_id"],
                "external_subject_id": record["external_subject_id"],
                "phenotype": record["phenotype"],
                "quality": record["quality"],
                "source": record["source"],
                "project_name": record["project_name"],
                "project_owner": record["project_owner"],
                "experiment_id": record["experiment_id"],
                "type": record["type"],
                "assay": record["assay"],
                "override_cycles": record["override_cycles"],
                "workflow": record["workflow"],
                "coverage": record["coverage"],
                "truseqindex": record.get("truseqindex", None),
            }

            # We will use the manual get and create approach
            try:
                # Check if the latest record is up to date
                obj = Library.objects.get_single(**df_object)
                continue
            except Library.DoesNotExist:
                # if latest record is missing/not up to date, insert a new one
                obj = Library(timestamp=df_timestamp, **df_object)
                obj.save()

                # Add the append counter
                rows_created.append(obj)

        except Exception as e:
            if any(record.values()):  # silent off iff blank row
                logger.warning(
                    f"Invalid record: {libjson.dumps(record)} Exception: {e}"
                )
                rows_invalid.append(record)
            continue

    return {
        "library_row_created_count": len(rows_created),
        "library_row_invalid_count": len(rows_invalid),
    }


def download_library(year: str) -> pd.DataFrame:
    """Download the full original library from which to extract the required information

    :param year: the sheet in the library spreadsheet to load
    """
    lab_sheet_id = libssm.get_secret(TRACKING_SHEET_ID)
    account_info = libssm.get_secret(GDRIVE_SERVICE_ACCOUNT)

    return libgdrive.download_sheet(account_info, lab_sheet_id, sheet=year)


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    clean a dataframe of lablibrary from a tracking sheet to correspond to the django object model
    we do this by editing the columns to match the django object
    """
    # remove unnamed
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # simplify verbose column names
    df = df.rename(
        columns={
            "Coverage (X)": "coverage",
            "TruSeq Index, unless stated": "truseqindex",
        }
    )

    # convert PascalCase headers to snake_case and fix ID going to _i_d
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    df = df.rename(columns=lambda x: pattern.sub("_", x).lower().replace("_i_d", "_id"))

    return df


def _clean_data_cell(value):
    if isinstance(value, str):
        value = value.strip()

    # python NaNs are != to themselves
    if value == "_" or value == "-" or value == np.nan or value != value:
        value = ""

    return value
