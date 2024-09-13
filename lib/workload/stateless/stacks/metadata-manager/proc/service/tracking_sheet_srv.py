import os
import re
import json

import pandas as pd
import numpy as np
from django.db import transaction

from libumccr import libgdrive
from libumccr.aws import libssm

import logging

from app.models import Subject, Sample, Library,Project,Contact
from app.models.library import Quality, LibraryType, Phenotype, WorkflowType
from app.models.sample import Source
from app.models.utils import get_value_from_human_readable_label
from proc.service.utils import clean_model_history

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SSM_NAME_TRACKING_SHEET_ID = os.getenv('SSM_NAME_TRACKING_SHEET_ID', '')
SSM_NAME_GDRIVE_ACCOUNT = os.getenv('SSM_NAME_GDRIVE_ACCOUNT', '')


@transaction.atomic
def persist_lab_metadata(df: pd.DataFrame, sheet_year: str):
    """
    Persist metadata records from a pandas dataframe into the db

    Args:
        df (pd.DataFrame): The source of truth for the metadata in this particular year
        sheet_year (type): The year for the metadata df supplied

    """
    logger.info(f"Start processing LabMetadata")

    # Used for statistics
    library_created = list()
    library_updated = list()
    library_deleted = list()
    sample_created = list()
    sample_updated = list()
    sample_deleted = list()
    subject_created = list()
    subject_updated = list()
    subject_deleted = list()

    rows_invalid = list()

    # The data frame is to be the source of truth for the particular year
    # So we need to remove db records which are not in the data frame
    # Only doing this for library records and (dangling) sample/subject may be removed on a separate process

    # For the library_id we need craft the library_id prefix to match the year
    # E.g. year 2024, library_id prefix is 'L24' as what the Lab tracking sheet convention
    library_prefix = f'L{sheet_year[-2:]}'
    for lib in Library.objects.filter(library_id__startswith=library_prefix).exclude(
            library_id__in=df['library_id'].tolist()).iterator():
        library_deleted.append(lib)
        lib.delete()

    # this the where records are updated, inserted, linked based on library_id
    for record in df.to_dict('records'):
        try:
            # 1. update or create all data in the model from the given record
            subject, is_sub_created, is_sub_updated = Subject.objects.update_or_create_if_needed(
                search_key={"subject_id": record.get('subject_id')},
                data={
                    "subject_id": record.get('subject_id'),
                    "external_subject_id": record.get('external_subject_id'),
                }
            )
            if is_sub_created:
                subject_created.append(subject)
            if is_sub_updated:
                subject_updated.append(subject)

            sample, is_smp_created, is_smp_updated = Sample.objects.update_or_create_if_needed(
                search_key={"sample_id": record.get('sample_id')},
                data={
                    "sample_id": record.get('sample_id'),
                    "external_sample_id": record.get('external_sample_id'),
                    "source": get_value_from_human_readable_label(Source.choices, record.get('source')),
                }
            )
            if is_smp_created:
                sample_created.append(sample)
            if is_smp_updated:
                sample_updated.append(sample)

            contact, _is_cnt_created, _is_cnt_updated = Contact.objects.update_or_create_if_needed(
                search_key={"contact_id": record.get('project_owner')},
                data={
                    "contact_id": record.get('project_owner'),
                }
            )

            project, _is_prj_created, _is_prj_updated = Project.objects.update_or_create_if_needed(
                search_key={"project_id": record.get('project_name')},
                data={
                    "project_id": record.get('project_name'),
                    "contact_id": contact.orcabus_id,
                }
            )

            library, is_lib_created, is_lib_updated = Library.objects.update_or_create_if_needed(
                search_key={"library_id": record.get('library_id')},
                data={
                    'library_id': record.get('library_id'),
                    'phenotype': get_value_from_human_readable_label(Phenotype.choices, record.get('phenotype')),
                    'workflow': get_value_from_human_readable_label(WorkflowType.choices, record.get('workflow')),
                    'quality': get_value_from_human_readable_label(Quality.choices, record.get('quality')),
                    'type': get_value_from_human_readable_label(LibraryType.choices, record.get('type')),
                    'assay': record.get('assay'),
                    'coverage': sanitize_library_coverage(record.get('coverage')),

                    # relationships
                    'sample_id': sample.orcabus_id,
                    'subject_id': subject.orcabus_id,
                    'project_id': project.orcabus_id,

                }
            )
            if is_lib_created:
                library_created.append(library)
            if is_lib_updated:
                library_updated.append(library)

        except Exception as e:
            if any(record.values()):  # silent off blank row
                print(f"Invalid record ({e}): {json.dumps(record, indent=2)}")
                rows_invalid.append(record)
            continue

    # clean up history for django-simple-history model if any
    clean_model_history()

    return {
        "library": {
            "new_count": len(library_created),
            "update_count": len(library_updated),
            "delete_count": len(library_deleted)
        },
        "sample": {
            "new_count": len(sample_created),
            "update_count": len(sample_updated),
            "delete_count": len(sample_deleted)

        },
        "subject": {
            "new_count": len(subject_created),
            "update_count": len(subject_updated),
            "delete_count": len(subject_deleted)

        },
        'invalid_record_count': len(rows_invalid),
    }


def download_tracking_sheet(year: str) -> pd.DataFrame:
    """
    Download the full original metadata from Google tracking sheet
    """
    sheet_id = libssm.get_secret(SSM_NAME_TRACKING_SHEET_ID)
    account_info = libssm.get_secret(SSM_NAME_GDRIVE_ACCOUNT)

    frames = []
    logger.info(f"Downloading {year} sheet")
    sheet_df = libgdrive.download_sheet(account_info, sheet_id, year)
    sheet_df = sanitize_lab_metadata_df(sheet_df)

    frames.append(sheet_df)

    df: pd.DataFrame = pd.concat(frames)
    return df


def sanitize_lab_metadata_df(df: pd.DataFrame):
    """
    sanitize record by renaming columns, and clean df cells
    """

    df = clean_columns(df)
    df = df.map(_clean_data_cell)

    # dropping any rows that library_id == ''
    df = df.drop(df[df.library_id.isnull()].index, errors='ignore')

    # dropping column that has empty column heading
    df = df.drop('', axis='columns', errors='ignore')

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
    clean a dataframe of labmetadata from a tracking sheet to correspond to the django object model
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


def _clean_data_cell(value):
    if isinstance(value, str):
        value = value.strip()

    # python NaNs are != to themselves
    if value == 'NA' or value == '_' or value == '-' or value == '' or value != value or value == np.nan:
        value = None

    return value


def sanitize_library_coverage(value: str):
    """
    convert value that is valid in the tracking sheet to return a value that is recognizable by the Django Model
    """
    try:
        # making coverage is float-able type
        lib_coverage = float(value)
        return f'{lib_coverage}'

    except (ValueError, TypeError):
        return None
