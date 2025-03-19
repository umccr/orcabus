#!/usr/bin/env python3

"""
Get the fastq list row from the fastq set id
"""
from typing import Dict, List

from fastq_tools import get_fastq_set, FastqSet


def handler(event, context) -> Dict[str, List[str]]:
    fastq_set_obj: FastqSet = get_fastq_set(event['fastqSetId'])

    return {
        "fastqListRowIdList": list(map(
            lambda fastq_list_row_iter_: fastq_list_row_iter_['id'],
            fastq_set_obj['fastqSet']
        ))
    }
