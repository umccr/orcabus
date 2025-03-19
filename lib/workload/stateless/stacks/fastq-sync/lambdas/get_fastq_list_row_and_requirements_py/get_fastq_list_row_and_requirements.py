#!/usr/bin/env python3

"""
Given a fastq list row and remaining requirements dict, determine which requirements are met by the object and which ones are not.

Given a dictionary as follows

{
    "fastqListRowId": "fqr.1234",
    "requirements": [
        "activeReadSet",
        "hasQc",
        "hasFingerprint"
    ]
}

We return a dictionary like the following
{
    "fastqListRowId": "fqr.1234",
    "satisfiedRequirements": [
        "activeReadSet",
        "hasQc"
    ],
    "unsatisfiedRequirements": [
        "hasFingerprint"
    ]
}
"""


from fastq_tools import get_fastq
from fastq_sync_tools import check_fastq_list_row_against_requirements_list


def handler(event, context):
    """
    Given a fastq list row and a list of requirements,
    determine which requirements are met by the object and which ones are not.
    :param event:
    :param context:
    :return:
    """
    fastq_obj = get_fastq(event['fastqListRowId'], includeS3Details=True)

    satisfied_requirements, unsatisfied_requirements = check_fastq_list_row_against_requirements_list(fastq_obj, event['requirements'])

    return {
        "fastqListRowObj": fastq_obj,
        "satisfiedRequirements": list(map(lambda req_iter_: req_iter_.value, satisfied_requirements)),
        "unsatisfiedRequirements": list(map(lambda req_iter_: req_iter_.value, unsatisfied_requirements))
    }
