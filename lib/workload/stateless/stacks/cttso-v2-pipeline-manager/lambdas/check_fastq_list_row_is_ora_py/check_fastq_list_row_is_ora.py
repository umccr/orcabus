#!/usr/bin/env python3

"""
Check fastq list row is ora
"""


def handler(event, context):
    """
    Collect the read1FileUri and read2FileUri from the fastq list and check if they are in the ora format,
    return True if they are, False otherwise
    :param event:
    :param context:
    :return:
    """

    # Get the fastq list from the event
    fastq_list_row = event['fastq_list_row']

    # Check if the read1FileUri and read2FileUri are in the ora format
    if fastq_list_row.get("read1FileUri").endswith(".ora") and fastq_list_row.get("read2FileUri").endswith(".ora"):
        return {
            "is_ora": True
        }
    elif fastq_list_row.get("read1FileUri").endswith(".gz") and fastq_list_row.get("read2FileUri").endswith(".gz"):
        return {
            "is_ora": False
        }
    else:
        raise ValueError("The read1FileUri and read2FileUri need to be in the same format")