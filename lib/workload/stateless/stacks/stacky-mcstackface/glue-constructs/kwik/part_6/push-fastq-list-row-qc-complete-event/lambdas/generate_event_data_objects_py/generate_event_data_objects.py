#!/usr/bin/env python3

"""
Generate the data outputs of the qc complete event

# Inputs are
fastq_list_row_id
sample_type
qc_metrics
library_internal_id

# So outputs are
fastqListRowId
sampleType
qcMetrics
libraryInternalId

# Then if sampleType is equal to WGS
duplicationRate
genomeCoverage

# Otherwise if sampleType is equal to WTS
exonFoldCoverage
"""

# Imports
import logging
from typing import Dict

# Set log level
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context) -> Dict[str, Dict[str, str]]:
    """
    :param event:
    :param context:
    :return:
    """

    # Get the inputs
    fastq_list_row_id = event['fastq_list_row_id']
    sample_type = event['sample_type']
    qc_metrics = event['qc_metrics']
    library_internal_id = event['library_internal_id']

    # Initialise output dict
    event_output_dict = {
        "fastqListRowId": fastq_list_row_id,
        "sampleType": sample_type,
        "libraryInternalId": library_internal_id
    }

    # Update dict per sample type
    if sample_type == "WGS":
        event_output_dict.update({
            "qcMetrics": {
                "duplicationRate": qc_metrics['duplication_rate'],
                "genomeCoverage": qc_metrics['genome_coverage']
            }
        })
    elif sample_type == "WTS":
        event_output_dict.update({
            "qcMetrics": {
                "exonFoldCoverage": qc_metrics['exon_fold_coverage']
            }
        })
    else:
        logger.error("Got sample_type as '{sample_type}', expected 'WGS' or 'WTS'")
        raise ValueError

    return {
        "event_output_dict": event_output_dict
    }
