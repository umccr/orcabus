#!/usr/bin/env python3

"""
Get the boolean parameters from the event input
"""
from typing import Dict


def handler(event, context) -> Dict[str, Dict]:
    """
    Get the boolean parameters from the event input
    :param event:
    :param context:
    :return: Dictionary of boolean parameters
    """

    # Collect the event data input
    event_data_input: Dict = event['event_data_input']

    # Get the boolean parameters from the event input
    cwl_parameter_dict: Dict = {
        "enable_map_align_somatic": True,
        "enable_map_align_output_somatic": event_data_input.get('enableMapAlignOutput', True),
        "enable_map_align_germline": True,
        "enable_map_align_output_germline": False,
        "enable_duplicate_marking": event_data_input.get('enableDuplicateMarking', True),
        "enable_cnv_somatic": event_data_input.get('enableCnvSomatic', None),
        "enable_hrd_somatic": event_data_input.get('enableHrdSomatic', None),
        "enable_sv_somatic": event_data_input.get('enableSvSomatic', None),
        "cnv_use_somatic_vc_baf": event_data_input.get('cnvUseSomaticVcBaf', None)
    }

    # Remove the None values from the dictionary
    cwl_parameter_dict = dict(
        filter(
            lambda kv: kv[1] is not None,
            cwl_parameter_dict.items()
        )
    )

    # Return the boolean parameters
    return {
        "boolean_parameters": cwl_parameter_dict
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "event_data_input": {
#                         "enableDuplicateMarking": True,
#                         "enableCnvSomatic": True,
#                         "enableHrdSomatic": True,
#                         "enableSvSomatic": True,
#                         "cnvUseSomaticVcBaf": True,
#                         "outputPrefixSomatic": "L2400195",
#                         "outputPrefixGermline": "L2400191",
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
#     #     "boolean_parameters": {
#     #         "enable_duplicate_marking": true,
#     #         "enable_cnv_somatic": true,
#     #         "enable_hrd_somatic": true,
#     #         "enable_sv_somatic": true,
#     #         "cnv_use_somatic_vc_baf": true,
#     #         "enable_map_align_output_somatic": true,
#     #         "enable_map_align_output_germline": false
#     #     }
#     # }
