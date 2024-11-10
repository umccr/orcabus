#!/usr/bin/env python3

"""
Generate draft event payload for the event

Given the tumor library id and normal library id, generate the inputs for the workflow.

{
   "inputs": {
     "mode": "wgts | targeted"
     "analysis_type": "DNA | RNA | DNA/RNA"
     "subject_id": "<subject_id>", // Required
     "tumor_rna_sample_id": "<rna_sample_id>",  // Required if analysis_type is set to RNA
     "tumor_rna_fastq_uri_list": [ <Array of wts fastq list rows> ]  // Required if analysis_type is set to RNA
   },
   "tags": {
      "tumorRnaLibraryId": "<rna_sample_id>", // Present if analysis_type is set to RNA
      "subjectId": "<subject_id>",
      "individualId": "<individual_id>",
   }
}

"""

# GLOBALS
MODE = "wgts"
ANALYSIS_TYPE = "RNA"

# Functions
from typing import Dict, List


def handler(event, context) -> Dict:
    """
    Generate draft event payload for the event
    :param event: event object
    :return: draft event payload
    """

    tumor_library_id = event['tumor_library_id']
    subject_id = event['subject_id']
    individual_id = event['individual_id']
    tumor_fastq_list_rows: List[Dict] = event['tumor_fastq_list_rows']
    tumor_fastq_list_row_ids: List[str] = event['tumor_fastq_list_row_ids']

    return {
        "input_event_data": {
            "mode": MODE,
            "analysisType": ANALYSIS_TYPE,
            "subjectId": subject_id.replace(" ", "_"),
            "tumorRnaSampleId": tumor_library_id,
            "tumorRnaFastqListRows": tumor_fastq_list_rows,
        },
        "event_tags": {
            "subjectId": subject_id,
            "individualId": individual_id,
            "libraryId": tumor_library_id,
            "fastqListRowIds": tumor_fastq_list_row_ids,
        }
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "tumor_fastq_list_row_ids": [
#                         "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254"
#                     ],
#                     "subject_id": "218-007",
#                     "tumor_fastq_list_rows": [
#                         {
#                             "rgid": "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254",
#                             "rgsm": "L2400254",
#                             "rglb": "L2400254",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#                         }
#                     ],
#                     "tumor_library_id": "L2400254",
#                     "individual_id": "SBJ04661"
#                 },
#                 None
#             ), indent=4
#         )
#     )
#     # {
#     #     "input_event_data": {
#     #         "mode": "wgts",
#     #         "analysisType": "RNA",
#     #         "subjectId": "218-007",
#     #         "tumorRnaSampleId": "L2400254",
#     #         "tumorRnaFastqUriList": [
#     #             "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#     #             "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#     #         ]
#     #     },
#     #     "event_tags": {
#     #         "subjectId": "218-007",
#     #         "individualId": "SBJ04661",
#     #         "libraryId": "L2400254",
#     #         "fastqListRowIds": [
#     #             "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254"
#     #         ]
#     #     }
#     # }
