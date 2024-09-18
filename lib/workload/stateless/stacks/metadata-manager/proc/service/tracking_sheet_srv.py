import os
import re
import json

import pandas as pd
import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from libumccr import libgdrive
from libumccr.aws import libssm

import logging

from app.models import Subject, Sample, Library, Project, Contact, Individual
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
    stats = {
        "library": {
            "create_count": 0,
            "update_count": 0,
            "delete_count": 0,
        },
        "sample": {
            "create_count": 0,
            "update_count": 0,
            "delete_count": 0,

        },
        "subject": {
            "create_count": 0,
            "update_count": 0,
            "delete_count": 0,
        },
        "individual": {
            "create_count": 0,
            "update_count": 0,
            "delete_count": 0,
        },
        "project": {
            "create_count": 0,
            "update_count": 0,
            "delete_count": 0,
        },
        "contact": {
            "create_count": 0,
            "update_count": 0,
            "delete_count": 0,
        },
        'invalid_record_count': 0,
    }

    # The data frame is to be the source of truth for the particular year
    # So we need to remove db records which are not in the data frame
    # Only doing this for library records and (dangling) sample/subject may be removed on a separate process

    # For the library_id we need craft the library_id prefix to match the year
    # E.g. year 2024, library_id prefix is 'L24' as what the Lab tracking sheet convention
    library_prefix = f'L{sheet_year[-2:]}'
    for lib in Library.objects.filter(library_id__startswith=library_prefix).exclude(
            library_id__in=df['library_id'].tolist()).iterator():
        stats['library']['delete_count'] += 1
        lib.delete()

    # this the where records are updated, inserted, linked based on library_id
    for record in df.to_dict('records'):
        try:
            # 1. update or create all data in the model from the given record

            # ------------------------------
            # Individual
            # ------------------------------
            idv, is_idv_created, is_idv_updated = Individual.objects.update_or_create_if_needed(
                search_key={
                    "individual_id": record.get('subject_id'),
                    "source": "lab"
                },
                data={
                    "individual_id": record.get('subject_id'),
                    "source": "lab"
                }
            )
            if is_idv_created:
                stats['individual']['create_count'] += 1
            if is_idv_updated:
                stats['individual']['update_count'] += 1

            # ------------------------------
            # Subject: We map the external_subject_id to the subject_id in the model
            # ------------------------------
            subject, is_sub_created, is_sub_updated = Subject.objects.update_or_create_if_needed(
                search_key={"subject_id": record.get('external_subject_id')},
                data={
                    "subject_id": record.get('external_subject_id'),
                }
            )

            if is_sub_created:
                stats['subject']['create_count'] += 1
            if is_sub_updated:
                stats['subject']['update_count'] += 1

            # link individual to external subject
            try:
                subject.individual_set.get(orcabus_id=idv.orcabus_id)
            except ObjectDoesNotExist:
                subject.individual_set.add(idv)

                # We update the stats when new idv is linked to sbj, only if this is not recorded as
                # update/create in previous upsert method
                if not is_sub_created and not is_sub_updated:
                    stats['subject']['update_count'] += 1

            # ------------------------------
            # Sample
            # ------------------------------
            sample, is_smp_created, is_smp_updated = Sample.objects.update_or_create_if_needed(
                search_key={"sample_id": record.get('sample_id')},
                data={
                    "sample_id": record.get('sample_id'),
                    "external_sample_id": record.get('external_sample_id'),
                    "source": get_value_from_human_readable_label(Source.choices, record.get('source')),
                }
            )
            if is_smp_created:
                stats['sample']['create_count'] += 1
            if is_smp_updated:
                stats['sample']['create_update'] += 1

            # ------------------------------
            # Contact
            # ------------------------------
            contact, _is_ctc_created, _is_ctc_updated = Contact.objects.update_or_create_if_needed(
                search_key={"contact_id": record.get('project_owner')},
                data={
                    "contact_id": record.get('project_owner'),
                }
            )

            # ------------------------------
            # Project: Upsert project with contact as part of the project
            # ------------------------------
            project, is_prj_created, is_prj_updated = Project.objects.update_or_create_if_needed(
                search_key={"project_id": record.get('project_name')},
                data={
                    "project_id": record.get('project_name'),
                }
            )
            # link project to its contact
            try:
                project.contact_set.get(orcabus_id=contact.orcabus_id)
            except ObjectDoesNotExist:
                project.contact_set.add(contact)

                # We update the stats when new ctc is linked to prj, only if this is not recorded as
                # update/create in previous upsert method
                if not is_prj_created and not is_prj_updated:
                    stats['project']['update_count'] += 1

            # ------------------------------
            # Library: Upsert library record with related sample, subject, project
            # ------------------------------
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
                }
            )
            if is_lib_created:
                stats['library']['create_count'] += 1
            if is_lib_updated:
                stats['library']['update_count'] += 1

            # link library to its project
            try:
                library.project_set.get(orcabus_id=project.orcabus_id)
            except ObjectDoesNotExist:
                library.project_set.add(project)

                # We update the stats when new project is linked to library, only if this is not recorded as
                # update/create in previous upsert method
                if not is_lib_created and not is_lib_updated:
                    stats['library']['update_count'] += 1

        except Exception as e:
            if any(record.values()):
                logger.warning(f"Invalid record ({e}): {json.dumps(record, indent=2)}")
                stats['invalid_record_count'] += 1
            continue

    # clean up history for django-simple-history model if any
    # Only clean for the past 15 minutes as this is what the maximum lambda cutoff
    clean_model_history(minutes=15)

    return stats


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
