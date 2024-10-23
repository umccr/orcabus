#!/usr/bin/env python3

"""
Clean up the fastq list rows
* convert uppercase to lowercase
* extend rgid to contain the instrument run and the sample name

* Otherwise very hard to match the fastq files to the sample names

#                      [
#                         {
#                             "RGID": "GAATTCGT.TTATGAGT.1",
#                             "RGSM": "L2400102",
#                             "RGLB": "L2400102",
#                             "Lane": 1,
#                             "Read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTGACGTT.TCCCAGAT.4",
#                             "RGSM": "L2400257",
#                             "RGLB": "L2400257",
#                             "Lane": 4,
#                             "Read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#                         }
#                     ]

To

#                      [
#                         {
#                             "rgid": "GAATTCGT.TTATGAGT.1.240229_A00130_0288_BH5HM2DSXC.L2400102",
#                             "rgsm": "L2400102",
#                             "rglb": "L2400102",
#                             "lane": 1,
#                             "read1fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "read2fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GTGACGTT.TCCCAGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400257",
#                             "rgsm": "L2400257",
#                             "rglb": "L2400257",
#                             "lane": 4,
#                             "read1fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#                             "read2fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#                         }
#                     ]
"""

from typing import Dict


def handler(event, context) -> Dict:
    """

    Given the instrument run id and fastq list rows, return the fastq list rows with the rgid
    extended to contain the instrument run id and the sample name

    All keys should be from UPPERCASE / PascalCase to camelCase

    :param event:
    :param context:
    :return:
    """

    # Get inputs
    instrument_run_id = event["instrument_run_id"]
    fastq_list_rows = event["fastq_list_rows"]

    # Clean up the fastq list rows
    fastq_list_rows = list(
        map(
            lambda fastq_list_row_iter_: {
                "rgid": f"{fastq_list_row_iter_['RGID']}.{instrument_run_id}.{fastq_list_row_iter_['RGSM']}",
                "rgsm": fastq_list_row_iter_["RGSM"],
                "rglb": fastq_list_row_iter_["RGLB"],
                "lane": fastq_list_row_iter_["Lane"],
                "read1FileUri": fastq_list_row_iter_["Read1FileUri"],
                "read2FileUri": fastq_list_row_iter_["Read2FileUri"]
            },
            fastq_list_rows
        )
    )

    # Return the fastq list rows
    return {
        "fastq_list_rows": fastq_list_rows
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "instrument_run_id": "240229_A00130_0288_BH5HM2DSXC",
#                     "fastq_list_rows": [
#                         {
#                             "RGID": "GAATTCGT.TTATGAGT.1",
#                             "RGSM": "L2400102",
#                             "RGLB": "L2400102",
#                             "Lane": 1,
#                             "Read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTGACGTT.TCCCAGAT.4",
#                             "RGSM": "L2400257",
#                             "RGLB": "L2400257",
#                             "Lane": 4,
#                             "Read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#                         }
#                     ]
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "fastq_list_rows": [
#     #         {
#     #             "rgid": "GAATTCGT.TTATGAGT.1.240229_A00130_0288_BH5HM2DSXC.L2400102",
#     #             "rgsm": "L2400102",
#     #             "rglb": "L2400102",
#     #             "lane": 1,
#     #             "read1fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#     #             "read2fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GTGACGTT.TCCCAGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400257",
#     #             "rgsm": "L2400257",
#     #             "rglb": "L2400257",
#     #             "lane": 4,
#     #             "read1fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#     #             "read2fileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#     #         }
#     #     ]
#     # }
