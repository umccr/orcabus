#!/usr/bin/env python3

"""
Add ora reference
"""
from pathlib import Path
from typing import Dict, Optional, List


def handler(event, context) -> Dict[str, bool]:
    """
    Get the boolean parameters from the event input
    :param event:
    :param context:
    :return: Dictionary of boolean parameters
    """

    # Collect the event data input
    event_data_input: Dict = event['event_data_input']

    # Get the fastq list rows
    tumor_fastq_list_rows: Optional[List] = event_data_input.get('tumorFastqListRows', None)
    normal_fastq_list_rows: Optional[List] = event_data_input.get('fastqListRows', None)

    # If tumorFastqListRows is None and fastqListRows is None, return false
    if tumor_fastq_list_rows is None and normal_fastq_list_rows is None:
        return {
            "add_ora_step": False,
            "is_hybrid": False
        }

    add_ora_step = False
    for fastq_list_row_iter in [tumor_fastq_list_rows, normal_fastq_list_rows]:
        if fastq_list_row_iter is not None:
            # If fastqListRows is not None, return true
            # Iterate over each of the fastq list rows, if one of the read1FileUri or read2FileUri end with .fastq.ora
            # return true
            if any(
                    [
                        row.get('read1FileUri', '').endswith('.fastq.ora') or
                        row.get('read2FileUri', '').endswith('.fastq.ora')
                        for row in fastq_list_row_iter
                    ]
            ):
                add_ora_step = True

    # Check if hybrid
    endings = []
    for fastq_list_row_iter in [tumor_fastq_list_rows, normal_fastq_list_rows]:
        if fastq_list_row_iter is not None:
            endings.extend(
                list(set(list(map(
                    lambda fastq_list_row_: Path(fastq_list_row_.get("read1FileUri")).suffix,
                    fastq_list_row_iter
                ))))
            )

    if len(list(set(endings))) > 1:
        # Don't need ora when hybrid since ora samples will be dropped
        is_hybrid = True
        add_ora_step = False
    else:
        is_hybrid = False

    # Got to here? Return false
    return {
        "add_ora_step": add_ora_step,
        "is_hybrid": is_hybrid
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "event_data_input": {
#                         "tumorFastqListRows": [
#                             {
#                                 "rgid": "ATGAGGCC.CAATTAAC.2",
#                                 "rgsm": "L2400195",
#                                 "rglb": "L2400195",
#                                 "lane": 2,
#                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#                             },
#                             {
#                                 "rgid": "ATGAGGCC.CAATTAAC.3",
#                                 "rgsm": "L2400195",
#                                 "rglb": "L2400195",
#                                 "lane": 3,
#                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#                             }
#                         ],
#                         "fastqListRows": [
#                             {
#                                 "rgid": "GCACGGAC.TGCGAGAC.4",
#                                 "rgsm": "L2400191",
#                                 "rglb": "L2400191",
#                                 "lane": 4,
#                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#                             }
#                         ],
#                         "dragenReferenceVersion": "v9-r3"
#                     }
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "add_ora_step": false,
#     #     "is_hybrid": false
#     # }
#
# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "event_data_input": {
#                         "tumorFastqListRows": [
#                             {
#                                 "rgid": "ATGAGGCC.CAATTAAC.2",
#                                 "rgsm": "L2400195",
#                                 "rglb": "L2400195",
#                                 "lane": 2,
#                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#                             },
#                             {
#                                 "rgid": "ATGAGGCC.CAATTAAC.3",
#                                 "rgsm": "L2400195",
#                                 "rglb": "L2400195",
#                                 "lane": 3,
#                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#                             }
#                         ],
#                         "fastqListRows": [
#                             {
#                                 "rgid": "GCACGGAC.TGCGAGAC.4",
#                                 "rgsm": "L2400191",
#                                 "rglb": "L2400191",
#                                 "lane": 4,
#                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.ora",
#                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.ora"
#                             }
#                         ],
#                         "dragenReferenceVersion": "v9-r3"
#                     }
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "add_ora_step": true,
#     #     "is_hybrid": true
#     # }
