#!/usr/bin/env python3

"""
Sum coverages for each RGID in the list

If any of the coverages are null, we also determine if the library qc is complete and if an event should be raised.

"""
import json
from typing import Union, List, Dict


def handler(event, context) -> Dict:
    """
    Get the qc metrics list
    :param event:
    :param context:
    :return:
    """

    qc_metrics_list: List[Union[str, None]] = event.get('qc_metrics_list')
    sample_type: str = event.get('sample_type')

    all_fastq_list_row_ids_complete: bool = all(qc_metrics_list)

    if not all_fastq_list_row_ids_complete:
        return {
            "all_fastq_list_row_ids_qc_complete": False
        }

    # Convert the qc_metrics_list to a list of dictionaries
    qc_metrics_list: List[Dict] = [json.loads(qc_metrics) for qc_metrics in qc_metrics_list]

    if sample_type == 'WGS':
        genome_coverage_sum = sum(qc_iter['genome_coverage'] for qc_iter in qc_metrics_list)
        duplication_rate_avg = sum(qc_iter['duplication_rate'] for qc_iter in qc_metrics_list) / len(qc_metrics_list)
        return {
            "all_fastq_list_row_ids_qc_complete": True,
            "genome_coverage": genome_coverage_sum,
            "duplication_rate": duplication_rate_avg
        }
    elif sample_type == 'WTS':
        exon_fold_coverage_sum = sum(qc_iter['exon_fold_coverage'] for qc_iter in qc_metrics_list)
        return {
            "all_fastq_list_row_ids_qc_complete": True,
            "exon_fold_coverage": exon_fold_coverage_sum
        }
