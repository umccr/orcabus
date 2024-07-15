import os
import re
from typing import List

import pandas as pd
import numpy as np
from django.db import transaction

from libumccr import libgdrive, libjson
from libumccr.aws import libssm

import logging

from app.models import Subject, Specimen, Library
from app.models.lab.library import Quality, LibraryType, Phenotype, WorkflowType
from app.models.lab.specimen import Source
from app.models.lab.utils import get_value_from_human_readable_label
from proc.service.utils import clean_model_history

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SSM_NAME_TRACKING_SHEET_ID = os.getenv('SSM_NAME_TRACKING_SHEET_ID', '')
SSM_NAME_GDRIVE_ACCOUNT = os.getenv('SSM_NAME_GDRIVE_ACCOUNT', '')


@transaction.atomic
def persist_lab_metadata(df: pd.DataFrame):
    """
    Persist metadata records from a pandas dataframe into the db

    :param df: dataframe to persist
    :return: result statistics - count of LabMetadata rows created
    """
    logger.info(f"Start processing LabMetadata")

    # Used for statistics
    library_created = list()
    library_updated = list()
    library_deleted = list()
    specimen_created = list()
    specimen_updated = list()
    specimen_deleted = list()
    subject_created = list()
    subject_updated = list()
    subject_deleted = list()

    rows_invalid = list()

    # If the df do not contain to what has existed in the db, it will be deleted
    for lib in Library.objects.exclude(internal_id__in=df['library_id'].tolist()).iterator():
        library_deleted.append(lib)
        lib.delete()

    for spc in Specimen.objects.exclude(internal_id__in=df['sample_id'].tolist()).iterator():
        specimen_deleted.append(spc)
        spc.delete()

    for sbj in Subject.objects.exclude(internal_id__in=df['subject_id'].tolist()).iterator():
        subject_deleted.append(sbj)
        sbj.delete()

    # Update: 12/07/2024. 'Subject' -> 'Specimen' is now ONE to Many, therefore the process of unliking the many to
    # many is not needed. The following code is commented for future reference when the 'Individual' concept is
    # introduced (which will have many-to-many as 'Individual' <-> 'Subject').

    # # removing relation of spc <-> sbj when needed as this is the many-to-many relationship
    # # adding relation between specimen and subject could be done per library records
    # # but removal will need all records to consider before the removing
    # # this `spc_sbj_df` will convert mapping between `sample_id` to all related `subject_id` as list
    # spc_sbj_df = df.loc[:, df.columns.isin(['sample_id', 'subject_id'])] \
    #     .groupby('sample_id')['subject_id'] \
    #     .apply(list) \
    #     .reset_index(name='subject_id_list')
    #
    # for record in spc_sbj_df.to_dict('records'):
    #     specimen_id = record.get("sample_id")
    #     subject_id_list = record.get("subject_id_list")
    #
    #     try:
    #         spc = Specimen.objects.get(internal_id=specimen_id)
    #         for sbj in spc.subjects.all().iterator():
    #             if sbj.internal_id not in subject_id_list:
    #                 spc.subjects.remove(sbj)
    #
    #     except ObjectDoesNotExist:
    #         pass
    #
    # ... added below...
    #
    # # specimen <-> subject (addition only)
    # try:
    #     specimen.subjects.get(id=subject.id)
    # except ObjectDoesNotExist:
    #     specimen.subjects.add(subject)

    # this the where records are updated, inserted, linked based on library_id
    for record in df.to_dict('records'):
        try:
            # 1. update or create all data in the model from the given record
            subject, is_sub_created = Subject.objects.update_or_create(
                internal_id=record.get('subject_id'),
                defaults={
                    "internal_id": record.get('subject_id')
                }
            )
            if is_sub_created:
                subject_created.append(subject)
            else:
                subject_updated.append(subject)

            specimen, is_spc_created = Specimen.objects.update_or_create(
                internal_id=record.get('sample_id'),
                defaults={
                    "internal_id": record.get('sample_id'),
                    "source": get_value_from_human_readable_label(Source.choices, record.get('source')),
                    'subject_id': subject.id
                }
            )
            if is_spc_created:
                specimen_created.append(specimen)
            else:
                specimen_updated.append(specimen)

            library, is_lib_created = Library.objects.update_or_create(
                internal_id=record.get('library_id'),
                defaults={
                    'internal_id': record.get('library_id'),
                    'phenotype': get_value_from_human_readable_label(Phenotype.choices, record.get('phenotype')),
                    'workflow': get_value_from_human_readable_label(WorkflowType.choices, record.get('workflow')),
                    'quality': get_value_from_human_readable_label(Quality.choices, record.get('quality')),
                    'type': get_value_from_human_readable_label(LibraryType.choices, record.get('type')),
                    'assay': record.get('assay'),
                    'coverage': sanitize_library_coverage(record.get('coverage')),
                    'specimen_id': specimen.id
                }
            )
            if is_lib_created:
                library_created.append(library)
            else:
                library_updated.append(library)

            # 2. linking or updating model to each other based on the record (update if it does not match)

            # library <-> specimen
            if library.specimen is None or library.specimen.id != specimen.id:
                library.specimen = specimen
                library.save()

            # specimen <-> subject
            if specimen.subject is None or specimen.subject.id != subject.id:
                specimen.subject = subject
                specimen.save()

        except Exception as e:
            if any(record.values()):  # silent off iff blank row
                logger.warning(f"Invalid record: {libjson.dumps(record)} Exception: {e}")
                rows_invalid.append(record)
            continue

    clean_model_history()

    return {
        "library": {
            "new_count": len(library_created),
            "update_count": len(library_updated),
            "delete_count": len(library_deleted)
        },
        "specimen": {
            "new_count": len(specimen_created),
            "update_count": len(specimen_updated),
            "delete_count": len(specimen_deleted)

        },
        "subject": {
            "new_count": len(subject_created),
            "update_count": len(subject_updated),
            "delete_count": len(subject_deleted)

        },
        'invalid_record_count': len(rows_invalid),
    }


def download_tracking_sheet(year_array: List[int]) -> pd.DataFrame:
    """
    Download the full original metadata from Google tracking sheet
    """
    sheet_id = libssm.get_secret(SSM_NAME_TRACKING_SHEET_ID)
    account_info = libssm.get_secret(SSM_NAME_GDRIVE_ACCOUNT)

    frames = []
    for i in year_array:
        year_str = str(i)
        logger.info(f"Downloading {year_str} sheet")
        sheet_df = libgdrive.download_sheet(account_info, sheet_id, year_str)
        sheet_df = sanitize_lab_metadata_df(sheet_df)

        # the year might be in the future therefore it does not exist
        if sheet_df.empty:
            break

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
