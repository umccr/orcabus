#!/usr/bin/env python3

"""
Given a set of list of fastq list row objects in the format

"RGID", "RGSM", "RGLB", "Lane", "Read1FileUri", "Read2FileUri",

Convert to a CWL input file format for the fastq list row objects.
"""

# Standard imports
import logging
from typing import Dict, Union

# Set logger
logging.basicConfig(
    level=logging.INFO,
    force=True,
    format='%(asctime)s %(message)s'
)
logger = logging.getLogger()


def pascal_case_to_snake_case(pascal_case_str: str) -> str:
    """
    Convert a PascalCase string to snake_case
    :param pascal_case_str:
    :return:
    """
    return ''.join(['_' + i.lower() if i.isupper() else i for i in pascal_case_str]).lstrip('_')


def get_key_value(key: str, fastq_list_row_dict: Dict) -> Union[str | int | Dict]:
    """
    Given a key, find the value in the fastq list row dict object,
    The key may be in any case, so we will convert the key to lowercase
    If the key is in
    :param key:
    :param fastq_list_row_dict:
    :return:
    """
    # Check for primitive types: rgid, rgsm, rglb, lane
    if key.startswith("rg"):
        fastq_list_row_key = next(
            filter(
                lambda key_iter: key_iter.lower() == key,
                fastq_list_row_dict.keys()
            )
        )
        return fastq_list_row_dict[fastq_list_row_key]

    # Check for lane
    if key.startswith("lane"):
        fastq_list_row_key = next(
            filter(
                lambda key_iter: key_iter.lower() == key,
                fastq_list_row_dict.keys()
            )
        )
        return int(fastq_list_row_dict[fastq_list_row_key])

    # Check for read file uri
    if key.startswith("read"):
        # Get the read number
        read_number = key[-1]  # Either 1 or 2

        # Find the key
        fastq_list_row_key = next(
            filter(
                lambda key_iter: (
                        pascal_case_to_snake_case(key_iter).startswith(key.replace("_", "")) and
                        read_number in key_iter
                ),
                fastq_list_row_dict.keys()
            )
        )
        return {
            "class": "File",
            "location": fastq_list_row_dict[fastq_list_row_key]
        }

    logger.error(f"Could not determine key '{key}' in fastq list row")
    raise KeyError


def convert_fastq_list_row_to_cwl_input(fastq_list_row: Dict) -> Dict:
    """
    Convert fastq list row to CWL
    :param fastq_list_row:
    :return:
    """

    cwl_fastq_list_row = {}

    # Check each rg value
    for rg_key in ["rgid", "rgsm", "rglb"]:
        if rg_key not in map(lambda key_iter: key_iter.lower(), fastq_list_row.keys()):
            logger.error("Could not find rgid in fastq list row")
            raise KeyError
        cwl_fastq_list_row[rg_key] = get_key_value(rg_key, fastq_list_row)

    # Get lane (as an int)
    if "lane" not in map(lambda key_iter: key_iter.lower(), fastq_list_row.keys()):
        logger.error("Could not find lane in fastq list row")
        raise KeyError
    cwl_fastq_list_row["lane"] = get_key_value("lane", fastq_list_row)

    # Get read_1 and read_2
    for read_iter in ["read_1", "read_2"]:
        if (
                f"{read_iter.replace('_', '')}_file_uri" not in
                map(lambda key_iter: pascal_case_to_snake_case(key_iter), fastq_list_row.keys())
        ):
            logger.error(f"Could not find {read_iter} in fastq list row")
            raise KeyError
        cwl_fastq_list_row[read_iter] = get_key_value(read_iter, fastq_list_row)

    logger.info(fastq_list_row)
    logger.info(cwl_fastq_list_row)

    return cwl_fastq_list_row


def handler(event, context):
    """
    Given a set of list of fastq list row objects in the format,
    convert to a CWL input file format for the fastq list row objects.

    :param event:
    :param context:
    :return:
    """
    if not event.get("fastq_list_rows"):
        logger.error("Could not get the attribute 'fastq_list_rows'")
        raise KeyError

    return {
        "fastq_list_rows": list(
            map(
                lambda fastq_list_row_iter: convert_fastq_list_row_to_cwl_input(fastq_list_row_iter),
                event["fastq_list_rows"]
            )
        )
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "fastq_list_rows": [
#                         {
#                             "rgid": "GAATTCGT.TTATGAGT.1",
#                             "rgsm": "L2400102",
#                             "rglb": "L2400102",
#                             "lane": 1,
#                             "read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GAGAATGGTT.TTGCTGCCGA.1",
#                             "rgsm": "L2400159",
#                             "rglb": "L2400159",
#                             "lane": 1,
#                             "read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#                             "read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#                         },
#                     ]
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # Output
#     # {
#     #   "fastq_list_rows": [
#     #     {
#     #       "rgid": "GAATTCGT.TTATGAGT.1",
#     #       "rgsm": "L2400102",
#     #       "rglb": "L2400102",
#     #       "lane": 1,
#     #       "read_1": {
#     #         "class": "File",
#     #         "location": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz"
#     #       },
#     #       "read_2": {
#     #         "class": "File",
#     #         "location": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #       }
#     #     },
#     #     {
#     #       "rgid": "GAGAATGGTT.TTGCTGCCGA.1",
#     #       "rgsm": "L2400159",
#     #       "rglb": "L2400159",
#     #       "lane": 1,
#     #       "read_1": {
#     #         "class": "File",
#     #         "location": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz"
#     #       },
#     #       "read_2": {
#     #         "class": "File",
#     #         "location": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#     #       }
#     #     }
#     #   ]
#     # }
