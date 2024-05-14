#!/usr/bin/env python3

"""
Handle directory outputs
"""

# Standard libraries
from pathlib import Path
from typing import Dict
import typing
import boto3

# Local libraries
from .globals import (
    ICAV2_CACHE_PROJECT_BCLCONVERT_OUTPUT_SSM_PATH,
    ICAV2_CACHE_PROJECT_ID_SSM_PATH
)
from .logger import get_logger

# Dev libraries
if typing.TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient


# Set logger
logger = get_logger()


def get_basespace_run_id_from_bssh_json_output(bssh_json_output: Dict) -> int:
    """
    From
    {
      ...
      "Projects": {
        "OutputProject": {
          "Name": "bssh_aps2-sh-prod_3593591"
        }
      }
    }

    To

    3593591
    :param bssh_json_output:
    :return:
    """
    return int(
        bssh_json_output
        .get("Projects")
        .get("OutputProject")
        .get("Name")
        .split("_")[-1]
    )


def get_year_from_run_id(run_id: str) -> str:
    """
    Convert 220101_A00111_0001_AH2Y7KDSXY to 2022
    :return:
    """
    return f"20{run_id.split('_')[0][0:2]}"


def get_month_from_run_id(run_id: str) -> str:
    """
    Convert 220102_A00111_0001_AH2Y7KDSXY to 01
    :param run_id:
    :return:
    """
    return run_id.split('_')[0][2:4]


def generate_bclconvert_output_folder_path(bclconvert_run_cache_path: Path, run_id: str, basespace_run_id: int, portal_run_id: str) -> Path:
    """
    Output is as follows
    # <bclconvert_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id>
    :param bclconvert_output_path_root:
    :param run_id:
    :param basespace_run_id:
    :param portal_run_id:

    :return:
    """
    return (
            bclconvert_run_cache_path /
            run_id /
            str(basespace_run_id) /
            portal_run_id
    )


