#!/usr/bin/env python3


# Set the fastq list rows

# Set the output file prefix

#!/usr/bin/env python3

"""
Generate draft event payload for the event

Given the tumor library id and normal library id, generate the inputs for the workflow.

{
    "output_prefix": "<tumor_library_id>",
    "tumor_fastq_list_rows": <tumor_fastq_list_rows>,
}

"""

from typing import Dict
DEFAULT_DRAGEN_REFERENCE_VERSION = "v9-r3"


def handler(event, context) -> Dict:
    """
    Generate draft event payload for the event
    :param event: event object
    :return: draft event payload
    """

    tumor_library_id = event['tumor_library_id']
    tumor_fastq_list_rows: Dict = event['tumor_fastq_list_rows']

    return {
        "input_event_data": {
            "outputPrefix": tumor_library_id,
            "tumorFastqListRows": tumor_fastq_list_rows,
        }
    }
