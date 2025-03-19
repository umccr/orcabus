#!/usr/bin/env python3

"""
Given a fastq set id and a set of requirements, check if the fastq set id meets the requirements.

We need to get all fastq list rows in the fastq set and from there, check if all fastq list row ids meet all requirements.

An example input is as follows:

{
    "fastqSetId": "fqs.12345",
    "requirements": [
        "activeReadSet",
        "hasQc",
        "hasFingerprint",
        "hasFileCompressionInformation"
    ]
}

An example output is as follows:

{
    "hasAllRequirements": true
}

We assume compression metadata is only required for readsets with ORA compression format

"""
from typing import Dict

from fastq_tools import get_fastq_set
from fastq_sync_tools import check_fastq_set_against_requirements_bool, Requirements


def handler(event, context) -> Dict[str, bool]:
    """
    Check if the fastq set id meets the requirements
    :param event:
    :param context:
    :return:
    """

    # Get the fastq set object
    fastq_set_obj = get_fastq_set(event["fastqSetId"], includeS3Details=True)

    # Get requirements
    requirements = list(map(lambda req_iter_: Requirements(req_iter_), event["requirements"]))

    return {
        "hasAllRequirements": check_fastq_set_against_requirements_bool(
            fastq_set_obj, requirements
        )
    }

