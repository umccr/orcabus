import os
import pandas as pd

from libumccr import libgdrive, libjson
from libumccr.aws import libssm

import logging

from proc.service.tracking_sheet_srv import download_tracking_sheet

logger = logging.getLogger()
logger.setLevel(logging.INFO)

YEAR_START = 2017

SSM_NAME_TRACKING_SHEET_ID = os.environ['SSM_NAME_TRACKING_SHEET_ID']
SSM_NAME_GDRIVE_ACCOUNT = os.environ['SSM_NAME_GDRIVE_ACCOUNT']


def handler(event, context):
    logger.info("Start processing update from google tracking sheet")

    sheet_id = libssm.get_secret(SSM_NAME_TRACKING_SHEET_ID)
    account_info = libssm.get_secret(SSM_NAME_GDRIVE_ACCOUNT)

    frames = []
    year = 2024
    while True:
        year_str = str(year)
        logger.info(f"Downloading {year_str} sheet")
        sheet_df = libgdrive.download_sheet(account_info, sheet_id, year_str)

        # the year might be in the future therefore it does not exist
        if sheet_df.empty:
            break

        frames.append(sheet_df)

        year += 1
        break

    df: pd.DataFrame = pd.concat(frames)

    df.drop(columns='', axis=1, inplace=True)
    print(df.head(10).to_json(orient="records"))
    #
    # print(df.to_json())
    # print(tracking_sheet_df.to_json())


#
#
# @transaction.atomic
# def persist_labmetadata(df: pd.DataFrame):
#     """
#     Persist labmetadata from a pandas dataframe into the db
#
#     Note that if table is truncated prior calling this then 'create' is implicit
#
#     :param df: dataframe to persist
#     :return: result statistics - count of LabMetadata rows created
#     """
#     logger.info(f"Start processing LabMetadata")
#
#     if df.empty:
#         return {
#             'message': "Empty data frame"
#         }
#
#     df = clean_columns(df)
#     df = df.applymap(_clean_data_cell)
#     df = df.drop_duplicates()
#     df = df.reset_index(drop=True)
#
#     rows_created = list()
#     rows_updated = list()
#     rows_invalid = list()
#
#     for record in df.to_dict('records'):
#         library_id = record.get('library_id') or None
#         try:
#             obj, created = LabMetadata.objects.update_or_create(
#                 library_id=library_id,
#                 defaults={
#                     'library_id': library_id,
#                     'sample_name': record.get('sample_name') or None,
#                     'sample_id': record.get('sample_id') or None,
#                     'external_sample_id': record['external_sample_id'],
#                     'subject_id': record['subject_id'],
#                     'external_subject_id': record['external_subject_id'],
#                     'phenotype': record['phenotype'],
#                     'quality': record['quality'],
#                     'source': record['source'],
#                     'project_name': record['project_name'],
#                     'project_owner': record['project_owner'],
#                     'experiment_id': record['experiment_id'],
#                     'type': record['type'],
#                     'assay': record['assay'],
#                     'override_cycles': record['override_cycles'],
#                     'workflow': record['workflow'],
#                     'coverage': record['coverage'],
#                     'truseqindex': record.get('truseqindex', None),
#                 }
#             )
#
#             if created:
#                 rows_created.append(obj)
#             else:
#                 rows_updated.append(obj)
#
#         except Exception as e:
#             if any(record.values()):  # silent off iff blank row
#                 logger.warning(f"Invalid record: {libjson.dumps(record)} Exception: {e}")
#                 rows_invalid.append(record)
#             continue
#
#     return {
#         'labmetadata_row_update_count': len(rows_updated),
#         'labmetadata_row_new_count': len(rows_created),
#         'labmetadata_row_invalid_count': len(rows_invalid),
#     }


if __name__ == '__main__':
    print('hello')
    handler({}, {})
