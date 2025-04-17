#!/usr/bin/env python3

"""
Given a fastq set id, return the fastq list row objects that are in the fastq set
"""

from typing import List, Dict

from fastq_tools import (
    get_fastq_set, FastqSet, FastqListRow
)


def handler(event, context) -> Dict[str, List[FastqListRow]]:
    """

    :param event:
    :param context:
    :return:
    """
    fastq_set_id = event.get("fastqSetId")

    if not fastq_set_id:
        raise ValueError("fastqSetId is required")

    return {
        "fastqListRows": get_fastq_set(fastq_set_id, includeS3Details=True)['fastqSet']
    }



