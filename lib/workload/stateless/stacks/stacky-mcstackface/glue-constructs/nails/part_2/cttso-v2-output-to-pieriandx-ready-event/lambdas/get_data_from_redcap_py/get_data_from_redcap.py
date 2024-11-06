#!/usr/bin/env python

"""
Given a library id, retrieve the necessary information from the REDCap database for this library id

We really only need the disease name if it exists
"""

# Standard imports
import logging
import typing
from typing import List
from time import sleep
from typing import Dict
from os import environ
import pandas as pd
import boto3
from botocore.exceptions import ClientError
import json
import pytz
from datetime import datetime

if typing.TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient

# Set logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)

# Globals
AUS_TIMEZONE = pytz.timezone("Australia/Melbourne")
AUS_TIME = datetime.now(AUS_TIMEZONE)
AUS_TIME_CURRENT_DEFAULT_DICT = {
    "date_accessioned": AUS_TIME.date().isoformat(),
    "date_collected": AUS_TIME.date().isoformat(),
    "time_collected": AUS_TIME.strftime("%H:%M"),
    "date_received": AUS_TIME.date().isoformat()
}
AUS_TIMEZONE_SUFFIX = AUS_TIME.strftime("%z")

REDCAP_RAW_FIELDS_CLINICAL: List = [
    "record_id",
    "clinician_firstname",
    "clinician_lastname",
    "patient_urn",
    "disease",
    "date_collection",
    "time_collected",
    "date_receipt",
    "id_sbj",
    "libraryid"
]

REDCAP_LABEL_FIELDS_CLINICAL: List = [
    "record_id",
    "report_type",
    "disease",
    "patient_gender",
    "id_sbj",
    "libraryid",
    "pierian_metadata_complete"
]


def get_lambda_client() -> 'LambdaClient':
    return boto3.client('lambda')


def get_redcap_lambda_from_env():
    """
    Get the redcap lambda from the environment
    :return:
    """
    return environ['REDCAP_LAMBDA_FUNCTION_NAME']


def warm_up_lambda():
    """
    Warm up the lambda function
    :return:
    """
    try:
        get_lambda_client().invoke(
            FunctionName=get_redcap_lambda_from_env(),
            InvocationType='RequestResponse'
        )
        return True
    except ClientError as e:
        print(f"Error warming up lambda: {e}")
        logger.info(f"Error warming up lambda: {e}")
        return False


def launch_redcap_raw_lambda(library_id: str) -> pd.DataFrame:
    """
    Launch the redcap lambda
    :param library_id:
    :return:
    """
    redcap_raw_df: pd.DataFrame = pd.DataFrame(columns=REDCAP_RAW_FIELDS_CLINICAL)

    raw_list: List = json.loads(
        json.loads(
            get_lambda_client().invoke(
                FunctionName=get_redcap_lambda_from_env(),
                InvocationType='RequestResponse',
                Payload=json.dumps(
                    {
                        "redcapProjectName": "TinyCT",
                        "queryStringParameters": {
                            "filter_logic": f"[libraryid] = \"{library_id}\"",
                            "fields": REDCAP_RAW_FIELDS_CLINICAL,
                            "raw_or_label": "raw",
                        }
                    }
                )
            )['Payload'].read()
        )['body']
    )

    # Concat the raw data to the redcap raw df
    redcap_raw_df = pd.concat(
        [
            redcap_raw_df,
            pd.DataFrame(raw_list, columns=REDCAP_RAW_FIELDS_CLINICAL)
        ]
    )

    # Rename columns
    redcap_raw_df.rename(
        columns={
            "clinician_firstname": "requesting_physician_first_name",
            "clinician_lastname": "requesting_physician_last_name",
            "libraryid": "library_id",
            "mrn": "patient_urn",
            "disease": "disease_id",
            "date_collection": "date_collected",
            "date_receipt": "date_received"
        },
        inplace=True
    )

    # Replace null values with NAs
    redcap_raw_df = redcap_raw_df.replace({None: pd.NA, "": pd.NA})

    return redcap_raw_df



def launch_redcap_label_lambda(library_id: str) -> pd.DataFrame:
    """
    Launch the redcap lambda
    :param library_id:
    :return:
    """
    redcap_label_df: pd.DataFrame = pd.DataFrame(columns=REDCAP_LABEL_FIELDS_CLINICAL)

    label_list: List = json.loads(
        json.loads(
            get_lambda_client().invoke(
                FunctionName=get_redcap_lambda_from_env(),
                InvocationType='RequestResponse',
                Payload=json.dumps(
                    {
                        "redcapProjectName": "TinyCT",
                        "queryStringParameters": {
                            "filter_logic": f"[libraryid] = \"{library_id}\"",
                            "fields": REDCAP_LABEL_FIELDS_CLINICAL,
                            "raw_or_label": "label",
                        }
                    }
                )
            )['Payload'].read()
        )['body']
    )

    # Concatenate dict with empty columns
    redcap_label_df = pd.concat(
        [
            redcap_label_df,
            pd.DataFrame(label_list, columns=REDCAP_LABEL_FIELDS_CLINICAL)
        ]
    )

    # Rename columns
    redcap_label_df.rename(
        columns={
            "report_type": "sample_type",
            "patient_gender": "gender",
            "disease": "disease_name",
            "libraryid": "library_id"
        },
        inplace=True
    )

    # Filter to select columns
    redcap_label_df = redcap_label_df[
        [
            "sample_type",
            "disease_name",
            "gender",
            "library_id",
            "pierian_metadata_complete"
        ]
    ]

    return redcap_label_df

def get_and_merge_raw_and_label_data(library_id: str) -> Dict:
    """
    Get the raw and label data from redcap and merge it
    :param library_id:
    :return:
    """
    redcap_raw_df = launch_redcap_raw_lambda(library_id)
    redcap_label_df = launch_redcap_label_lambda(library_id)

    # Check we have at least one entry
    if redcap_raw_df.shape[0] == 0:
        logger.info(f"No entries found for library '{library_id}'")
        raise ValueError

    # Update the date field with na values if not set (for validation samples only)
    validation_samples_index = redcap_label_df.query(
        "sample_type.str.lower()=='validation'"
    ).index
    # For clinical samples, we only need to update the time_collected field
    clinical_samples_index = redcap_label_df.query(
        "not sample_type=='validation'"
    ).index

    # Replace na values for date_collection or date_received, or date_receipt if None or null
    # Update time_collected field in both  since it might not exist
    # Update for validation samples
    for date_column in ["date_collected", "date_received", "time_collected"]:
        redcap_raw_df.loc[validation_samples_index, date_column] = \
            redcap_raw_df.loc[validation_samples_index, date_column].fillna(AUS_TIME_CURRENT_DEFAULT_DICT[date_column])
        # Update for clinical samples
    for date_column in ["time_collected"]:
        redcap_raw_df.loc[clinical_samples_index, date_column] = \
            redcap_raw_df.loc[clinical_samples_index, date_column].fillna(AUS_TIME_CURRENT_DEFAULT_DICT[date_column])

    # Update date fields
    redcap_raw_df["date_collected"] = redcap_raw_df.apply(
        lambda date_str: date_str.date_collected + "T" + date_str.time_collected + f":00{AUS_TIMEZONE_SUFFIX}",
        axis="columns"
    )

    # Add time to 'date_receipt' string
    redcap_raw_df["date_received"] = redcap_raw_df.apply(
        lambda x: x.date_received + f"T00:00:00{AUS_TIMEZONE_SUFFIX}",
        axis="columns"
    )

    # Subset columns for redcap raw df
    redcap_raw_df = redcap_raw_df[
        [
            "disease_id",
            "requesting_physicians_first_name",
            "requesting_physicians_last_name",
            "library_id",
            "date_collected",
            "date_received",
            "patient_urn"
        ]
    ]

    # Merge redcap data
    redcap_df: pd.DataFrame = pd.merge(
        redcap_raw_df, redcap_label_df,
        on=["library_id"]
    )

    # Merge redcap information and then return
    num_entries: int
    if not (num_entries := redcap_df.shape[0]) == 1:
        logger.info(f"Expected dataframe to be of length 1, not {num_entries}")
        raise ValueError(f"Expected dataframe to be of length 1, not {num_entries}")

    return redcap_df.to_dict(orient='records')[0]


def handler(event, context) -> Dict:
    """
    Handler for the lambda function
    :param event:
    :param context:
    :return:
    """
    # Wait for lambda to warm up
    logger.info("Warming up redcap lambda")
    while not warm_up_lambda():
        sleep(10)
    logger.info("Redcap lambda warmup complete!")

    # Return
    try:
        return {
            "redcap_data": get_and_merge_raw_and_label_data(event['library_id']),
            "in_redcap": True
        }
    except ValueError:
        return {
            "redcap_data": None,
            "in_redcap": False
        }


# if __name__ == '__main__':
#     # Or 'umccr-staging' / 'umccr-production'
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     # Or 'redcap-apis-stg-lambda-function' / 'redcap-apis-prod-lambda-function'
#     environ['REDCAP_LAMBDA_FUNCTION_NAME'] = 'redcap-apis-dev-lambda-function'
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "library_id": 'L2401380'
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )


# if __name__ == '__main__':
#     # Or 'umccr-staging' / 'umccr-production'
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     # Or 'redcap-apis-stg-lambda-function' / 'redcap-apis-prod-lambda-function'
#     environ['REDCAP_LAMBDA_FUNCTION_NAME'] = 'redcap-apis-dev-lambda-function'
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "library_id": "L2401529"
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
# # {
# #     "redcap_data": {
# #         "disease_id": 254637007,
# #         "requesting_physicians_first_name": "XXX",
# #         "requesting_physicians_last_name": "XXX",
# #         "library_id": "L2401380",
# #         "date_collected": "2024-09-06T23:00:00+1000",
# #         "date_received": "2024-09-06T00:00:00+1000",
# #         "patient_urn": "0038-61302",
# #         "sample_type": "Patient Care Sample",
# #         "disease_name": "Non-small cell lung cancer",
# #         "gender": "Unknown",
# #         "pierian_metadata_complete": "Complete"
# #     },
# #     "in_redcap": true
# # }
