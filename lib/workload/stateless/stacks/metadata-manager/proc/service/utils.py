import logging
import os
import re
import numpy as np
import pandas as pd
from django.core.management import call_command

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def clean_model_history(minutes: int = None):
    """
    The function will clean history for which where models have a history feature enabled

    When django uses the `save()` function, history table might be populated despite no changes (e.g.
    update_or_create). The history feature provided by django-simple-history track all signal that django sends to
    save model thus create duplicates. This clean function will remove these duplicates and only retain changes.

    Ref: https://django-simple-history.readthedocs.io/en/latest/utils.html
    """
    logger.info(f'removing duplicate history records for the last {minutes} minutes if any')
    call_command("clean_duplicate_history", "--auto", minutes=minutes, stdout=open(os.devnull, 'w'))


def sanitize_lab_metadata_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    sanitize record by renaming columns, and clean df cells
    """

    df = clean_columns(df)
    df = df.map(clean_data_cell)

    # dropping any rows that library_id == ''
    df = df.drop(df[df.library_id.isnull()].index, errors='ignore')

    # dropping column that has empty column heading
    df = df.drop('', axis='columns', errors='ignore')

    # We are now removing and '_rerun' or '_topup' postfix from libraries
    # See https://github.com/umccr/orcabus/issues/865
    df['library_id'] = df['library_id'].str.replace(r'_rerun\d*$', '', regex=True)
    df['library_id'] = df['library_id'].str.replace(r'_topup\d*$', '', regex=True)

    df = df.reset_index(drop=True)
    return df


def warn_drop_duplicated_library(df: pd.DataFrame) -> pd.DataFrame:
    """
    log warning messages if duplicated library_id found
    """
    # some warning for duplicates
    dup_lib_list = df[df.duplicated(subset=['library_id'], keep='last')]["library_id"].tolist()
    if len(dup_lib_list) > 0:
        logger.warning(f"data contain duplicate libraries: {', '.join(dup_lib_list)}")

    return df.drop_duplicates(subset=['library_id'], keep='last')


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    clean a dataframe from a tracking sheet to correspond to the django object model
    we do this by editing the columns to match the django object
    """
    # remove unnamed
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # simplify verbose column names
    df = df.rename(columns={'Coverage (X)': 'coverage', "TruSeq Index, unless stated": "truseqindex"})

    # convert PascalCase headers to snake_case and fix ID going to _i_d
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    df = df.rename(columns=lambda x: pattern.sub('_', x).lower().replace('_i_d', '_id'))

    return df


def clean_data_cell(value):
    if isinstance(value, str):
        value = value.strip()

    # python NaNs are != to themselves
    if value == 'NA' or value == '_' or value == '-' or value == '' or value != value or value == np.nan:
        value = None

    return value
