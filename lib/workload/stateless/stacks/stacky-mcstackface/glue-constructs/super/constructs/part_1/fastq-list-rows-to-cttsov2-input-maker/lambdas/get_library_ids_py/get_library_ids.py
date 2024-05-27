#!/usr/bin/env python3

"""
Custom script for each library id, generate a samplesheet and fastq list row set

"""


def get_samplesheet_for_tso500_library(library_id: str, samplesheet: Dict):
    return {
        "header": samplesheet.get("header"),
        "reads": samplesheet.get("reads"),
        "bclconvert_settings": {
            "adapter_read_1": "CTGTCTCTTATACACATCT",
            "adapter_read_2": "CTGTCTCTTATACACATCT",
            "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
            "mask_short_reads": 35,
            "adapter_behavior": "trim",
            "minimum_trimmed_read_length": 35
        },
        "bclconvert_data": list(
            filter(
                lambda library_id_iter: library_id_iter.get("sample_id") == library_id,
                samplesheet.get("bclconvert_data")
            )
        ),
        "tso500l_settings": {
            "adapter_read_1": "CTGTCTCTTATACACATCT",
            "adapter_read_2": "CTGTCTCTTATACACATCT",
            "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
            "mask_short_reads": 35,
            "adapter_behavior": "trim",
            "minimum_trimmed_read_length": 35
        },
        "tso500_data": list(
            filter(
                lambda library_id_iter: library_id_iter.get("sample_id") == library_id,
                samplesheet.get("tso500_data")
            )
        )
    }


def get_fastq_list_rows_for_library_id(library_id: str, fastq_list_rows: Dict):
    return list(
        filter(
            lambda fastq_list_row_iter: fastq_list_row_iter.get("RGSM") == library_id,
            fastq_list_rows
        )
    )


def handler(event, context):
    """
    Take in the fastq list rows, and samplesheet
    :param event:
    :param context:
    :return:
    """
    fastq_list_rows = event.get("fastq_list_rows")
    samplesheet = event.get("samplesheet")

    # Get tso500 library ids
    tso500_library_ids = list(
        set(
            list(
                map(
                    lambda tso500_data_iter: tso500_data_iter.get("sample_id"),
                    samplesheet.get("tso500_data")
                )
            )
        )
    )

    return {
        "library_id_map": tso500_library_ids
    }
