#!/usr/bin/env python3

"""
LAMBDA PLACEHOLDER: __convert_lims_json_list_to_csv_lambda_function_arn__

Intro:

Given a list of json files, convert them into a single csv file and return as a string
"""

# Imports
from typing import Dict
import pandas as pd

# Layer imports
from s3_json_tools import read_in_s3_json_objects_as_list

# Set logging
import logging
logger = logging.getLogger()
logger.setLevel("INFO")


def handler(event, context) -> Dict[str, str]:
    """
    Convert a list of files in a s3 bucket to a single csv file
    :param event:
    :param context:
    :return:
    """

    # Get inputs
    bucket = event.get('bucket', None)
    prefix = event.get('prefix', None)

    lims_row_json_df = pd.DataFrame(
        read_in_s3_json_objects_as_list(
            bucket=bucket,
            prefix=prefix
        )
    )

    return {
        "contents": lims_row_json_df.to_csv(index=False)
    }


# Test case
# FIXME