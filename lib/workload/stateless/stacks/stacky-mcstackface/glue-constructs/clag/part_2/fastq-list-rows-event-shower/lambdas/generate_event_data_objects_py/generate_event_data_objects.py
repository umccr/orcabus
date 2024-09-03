#!/usr/bin/env python3

"""
Given a set of fastq list rows, generate a set of event maps for each fastq file,
along with a create event shower as well
"""
from typing import Dict


def pascal_to_camel_case(pascal_str: str) -> str:
    """
    Convert a string from PascalCase to camelCase
    :param pascal_str:
    :return:
    """
    # If the string is empty, return an empty string
    if not pascal_str:
        return ""

    # If the string is only one character long, return the string
    if len(pascal_str) < 2:
        return pascal_str.lower()

    # Return the string as camel case
    return pascal_str[0].lower() + pascal_str[1:]


def generate_fastq_list_row_event(fastq_list_row: Dict, library: Dict, instrument_run_id: str) -> Dict:
    """
    Generate the fastq list row event

    :param fastq_list_row:
    :param instrument_run_id:
    :return:
    """

    # Get the new fastq list row dict
    new_fastq_list_row_dict = {}

    # Iterate through the fastq list row
    for key, value in fastq_list_row.items():
        if key.lower().startswith("rg") or key.lower() == "lane":
            new_fastq_list_row_dict[key.lower()] = value
            continue
        new_fastq_list_row_dict[pascal_to_camel_case(key)] = value

    fastq_list_row_rgid = '.'.join(
        [
            new_fastq_list_row_dict["rgid"],
            instrument_run_id,
            new_fastq_list_row_dict["rgsm"],
        ]
    )
    new_fastq_list_row_dict["rgid"] = fastq_list_row_rgid

    return {
        "fastqListRow": new_fastq_list_row_dict,
        "instrumentRunId": instrument_run_id,
        "library": {
            "libraryId": library.get("library_id"),
            "orcabusId": library.get("orcabus_id")
        }
    }


def handler(event, context):
    """
    Given a set of fastq list rows (and instrument run id), generate a set of event maps for each fastq file.
    :param event:
    :param context:
    :return:
    """

    # Get the fastq list rows and instrument run id
    fastq_list_rows = event['fastq_list_rows']
    library_obj_list = event['library_objs']
    instrument_run_id = event['instrument_run_id']

    # Generate the fastq list row events
    fastq_list_row_event_data_list = list(
        map(
            lambda fastq_list_row_iter: generate_fastq_list_row_event(
                fastq_list_row_iter,
                next(
                    filter(
                        lambda library_iter: library_iter['library_id'] == fastq_list_row_iter['RGSM'],
                        library_obj_list
                    )
                ),
                instrument_run_id
            ),
            fastq_list_rows
        )
    )

    # Generate the start and complete shower event data
    start_fastq_list_row_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    complete_fastq_list_row_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    # Generate project data level events
    project_list = list(
        set(
            map(
                lambda library_iter: (
                    library_iter.get("project_owner"), library_iter.get("project_name")
                ),
                library_obj_list
            )
        )
    )

    project_event_data_list = []
    for project_owner, project_name in project_list:
        project_event_data_list.append(
            {
                "event_data": {
                    "instrumentRunId": instrument_run_id,
                    "projectOwner": project_owner,
                    "projectName": project_name,
                    "libraries": list(
                        map(
                            lambda library_obj_iter: {
                                "orcabusId": library_obj_iter.get("orcabus_id"),
                                "libraryId": library_obj_iter.get("library_id"),
                                "fastqPairs": list(
                                    map(
                                        lambda fastq_list_row_event_data_iter: fastq_list_row_event_data_iter.get("fastqListRow"),
                                        filter(
                                            lambda fastq_list_row_event_data_iter: (
                                                    fastq_list_row_event_data_iter.get("library").get("libraryId") == library_obj_iter.get("library_id")
                                            ),
                                            fastq_list_row_event_data_list
                                        )
                                    )
                                )
                            },
                            filter(
                                lambda library_obj_iter: (
                                        library_obj_iter.get("project_owner") == project_owner and
                                        library_obj_iter.get("project_name") == project_name
                                ),
                                library_obj_list
                            )
                        )
                    )
                }
            }
        )

    # Return the event data
    return {
        "start_fastq_list_row_shower_event_data": start_fastq_list_row_shower_event_data,
        "project_event_data_list": project_event_data_list,
        "fastq_list_rows_event_data_list": fastq_list_row_event_data_list,
        "complete_fastq_list_row_shower_event_data": complete_fastq_list_row_shower_event_data,
    }


# Test the function
# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "library_objs": [
#                         {
#                             "library_id": "L2400102",
#                             "project_owner": "VCCC",
#                             "orcabus_id": "lib.01J5S9C4VMJ6PZ8GJ2G189AMXX",
#                             "project_name": "PO"
#                         },
#                         {
#                             "library_id": "L2400159",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBG0NF8QBNVKM6ESCD60",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400160",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBHP6NSB42RVFAP9PGJP",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400161",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBKCATYSFY40BRX6WJWX",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400162",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBN6EAXW4AXG7TQ1H6NC",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400163",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBQFX8V1QRW7KAV3MD1W",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400164",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBS64DNTHK6CE850CCNZ",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400165",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBTZRYQNTGAHPC2T601D",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400166",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CBX10204CK7EKGTH9TMB",
#                             "project_name": "Testing"
#                         },
#                         {
#                             "library_id": "L2400191",
#                             "project_owner": "TJohn",
#                             "orcabus_id": "lib.01J5S9CDF8HHG5PJE3ECJMKMY7",
#                             "project_name": "CAVATAK"
#                         },
#                         {
#                             "library_id": "L2400195",
#                             "project_owner": "TJohn",
#                             "orcabus_id": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S",
#                             "project_name": "CAVATAK"
#                         },
#                         {
#                             "library_id": "L2400196",
#                             "project_owner": "TJohn",
#                             "orcabus_id": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8",
#                             "project_name": "CAVATAK"
#                         },
#                         {
#                             "library_id": "L2400197",
#                             "project_owner": "TJohn",
#                             "orcabus_id": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ",
#                             "project_name": "CAVATAK"
#                         },
#                         {
#                             "library_id": "L2400198",
#                             "project_owner": "TJohn",
#                             "orcabus_id": "lib.01J5S9CDXCR7Q5K6A8VJRSMM4Q",
#                             "project_name": "CAVATAK"
#                         },
#                         {
#                             "library_id": "L2400231",
#                             "project_owner": "Tothill",
#                             "orcabus_id": "lib.01J5S9CFX5P69S4KZRQGDFKV1N",
#                             "project_name": "CUP"
#                         },
#                         {
#                             "library_id": "L2400238",
#                             "project_owner": "Tothill",
#                             "orcabus_id": "lib.01J5S9CGCAKQWHD9RBM9VXENY9",
#                             "project_name": "CUP"
#                         },
#                         {
#                             "library_id": "L2400239",
#                             "project_owner": "Tothill",
#                             "orcabus_id": "lib.01J5S9CGEM1DHRQP72EP09B2TA",
#                             "project_name": "CUP"
#                         },
#                         {
#                             "library_id": "L2400240",
#                             "project_owner": "Tothill",
#                             "orcabus_id": "lib.01J5S9CGG9N9GH5879SY6A6BJB",
#                             "project_name": "CUP"
#                         },
#                         {
#                             "library_id": "L2400241",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CGJ6G09YQ9KFHPSXMMVD",
#                             "project_name": "Control"
#                         },
#                         {
#                             "library_id": "L2400242",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CGKWDN7STKZKQM3KH9XR",
#                             "project_name": "Control"
#                         },
#                         {
#                             "library_id": "L2400249",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CH2SQ0P1SF7WAT5H4DSE",
#                             "project_name": "Control"
#                         },
#                         {
#                             "library_id": "L2400250",
#                             "project_owner": "Whittle",
#                             "orcabus_id": "lib.01J5S9CH4CYPA4SP05H8KRX4W9",
#                             "project_name": "BPOP-retro"
#                         },
#                         {
#                             "library_id": "L2400251",
#                             "project_owner": "Whittle",
#                             "orcabus_id": "lib.01J5S9CH65E4EE5QJEJ1C60GGG",
#                             "project_name": "BPOP-retro"
#                         },
#                         {
#                             "library_id": "L2400252",
#                             "project_owner": "Whittle",
#                             "orcabus_id": "lib.01J5S9CH7TGZMV39Z59WJ8H5GP",
#                             "project_name": "BPOP-retro"
#                         },
#                         {
#                             "library_id": "L2400253",
#                             "project_owner": "Whittle",
#                             "orcabus_id": "lib.01J5S9CH9TGMT2TJGBZX5VXHJY",
#                             "project_name": "BPOP-retro"
#                         },
#                         {
#                             "library_id": "L2400254",
#                             "project_owner": "Whittle",
#                             "orcabus_id": "lib.01J5S9CHBGAP2XSN4TG8SAMRYY",
#                             "project_name": "BPOP-retro"
#                         },
#                         {
#                             "library_id": "L2400255",
#                             "project_owner": "Tothill",
#                             "orcabus_id": "lib.01J5S9CHE4ERQ4H209DH397W8A",
#                             "project_name": "CUP"
#                         },
#                         {
#                             "library_id": "L2400256",
#                             "project_owner": "Tothill",
#                             "orcabus_id": "lib.01J5S9CHFXPDGYQ8TXHRWQR3PY",
#                             "project_name": "CUP"
#                         },
#                         {
#                             "library_id": "L2400257",
#                             "project_owner": "UMCCR",
#                             "orcabus_id": "lib.01J5S9CHHNGFJN73NPRQMSYGN9",
#                             "project_name": "Control"
#                         }
#                     ],
#                     "fastq_list_rows": [
#                         {
#                             "RGID": "GAATTCGT.TTATGAGT.1",
#                             "RGSM": "L2400102",
#                             "RGLB": "L2400102",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GAGAATGGTT.TTGCTGCCGA.1",
#                             "RGSM": "L2400159",
#                             "RGLB": "L2400159",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AGAGGCAACC.CCATCATTAG.1",
#                             "RGSM": "L2400160",
#                             "RGLB": "L2400160",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CCATCATTAG.AGAGGCAACC.1",
#                             "RGSM": "L2400161",
#                             "RGLB": "L2400161",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GATAGGCCGA.GCCATGTGCG.1",
#                             "RGSM": "L2400162",
#                             "RGLB": "L2400162",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGTTGACT.AGGACAGGCC.1",
#                             "RGSM": "L2400163",
#                             "RGLB": "L2400163",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TATTGCGCTC.CCTAACACAG.1",
#                             "RGSM": "L2400164",
#                             "RGLB": "L2400164",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TTCTACATAC.TTACAGTTAG.1",
#                             "RGSM": "L2400166",
#                             "RGLB": "L2400166",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGAGGCC.CAATTAAC.2",
#                             "RGSM": "L2400195",
#                             "RGLB": "L2400195",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACTAAGAT.CCGCGGTT.2",
#                             "RGSM": "L2400196",
#                             "RGLB": "L2400196",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.2",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TCGTAGTG.CCAAGTCT.2",
#                             "RGSM": "L2400231",
#                             "RGLB": "L2400231",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GGAGCGTC.GCACGGAC.2",
#                             "RGSM": "L2400238",
#                             "RGLB": "L2400238",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGCATG.GGTACCTT.2",
#                             "RGSM": "L2400239",
#                             "RGLB": "L2400239",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCAATGCA.AACGTTCC.2",
#                             "RGSM": "L2400240",
#                             "RGLB": "L2400240",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGAGGCC.CAATTAAC.3",
#                             "RGSM": "L2400195",
#                             "RGLB": "L2400195",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACTAAGAT.CCGCGGTT.3",
#                             "RGSM": "L2400196",
#                             "RGLB": "L2400196",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.3",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TCGTAGTG.CCAAGTCT.3",
#                             "RGSM": "L2400231",
#                             "RGLB": "L2400231",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GGAGCGTC.GCACGGAC.3",
#                             "RGSM": "L2400238",
#                             "RGLB": "L2400238",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGCATG.GGTACCTT.3",
#                             "RGSM": "L2400239",
#                             "RGLB": "L2400239",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCAATGCA.AACGTTCC.3",
#                             "RGSM": "L2400240",
#                             "RGLB": "L2400240",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACGCCTTGTT.ACGTTCCTTA.4",
#                             "RGSM": "L2400165",
#                             "RGLB": "L2400165",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCACGGAC.TGCGAGAC.4",
#                             "RGSM": "L2400191",
#                             "RGLB": "L2400191",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.4",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CTTGGTAT.GGACTTGG.4",
#                             "RGSM": "L2400198",
#                             "RGLB": "L2400198",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTTCCAAT.GCAGAATT.4",
#                             "RGSM": "L2400241",
#                             "RGLB": "L2400241",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACCTTGGC.ATGAGGCC.4",
#                             "RGSM": "L2400242",
#                             "RGLB": "L2400242",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AGTTTCGA.CCTACGAT.4",
#                             "RGSM": "L2400249",
#                             "RGLB": "L2400249",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GAACCTCT.GTCTGCGC.4",
#                             "RGSM": "L2400250",
#                             "RGLB": "L2400250",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCCCAGTG.CCGCAATT.4",
#                             "RGSM": "L2400251",
#                             "RGLB": "L2400251",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TGACAGCT.CCCGTAGG.4",
#                             "RGSM": "L2400252",
#                             "RGLB": "L2400252",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CATCACCC.ATATAGCA.4",
#                             "RGSM": "L2400253",
#                             "RGLB": "L2400253",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CTGGAGTA.GTTCGGTT.4",
#                             "RGSM": "L2400254",
#                             "RGLB": "L2400254",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GATCCGGG.AAGCAGGT.4",
#                             "RGSM": "L2400255",
#                             "RGLB": "L2400255",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AACACCTG.CGCATGGG.4",
#                             "RGSM": "L2400256",
#                             "RGLB": "L2400256",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTGACGTT.TCCCAGAT.4",
#                             "RGSM": "L2400257",
#                             "RGLB": "L2400257",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#                         }
#                     ],
#                     "instrument_run_id": "240229_A00130_0288_BH5HM2DSXC"
#                 }
#                 ,
#                 None
#             )
#             ,
#             indent=4
#         )
#     )
#
#     # {
#     #     "start_fastq_list_row_shower_event_data": {
#     #         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#     #     },
#     #     "project_event_data_list": [
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "projectOwner": "UMCCR",
#     #                 "projectName": "Testing",
#     #                 "libraries": [
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBG0NF8QBNVKM6ESCD60",
#     #                         "libraryId": "L2400159",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GAGAATGGTT.TTGCTGCCGA.1.240229_A00130_0288_BH5HM2DSXC.L2400159",
#     #                                 "rgsm": "L2400159",
#     #                                 "rglb": "L2400159",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBHP6NSB42RVFAP9PGJP",
#     #                         "libraryId": "L2400160",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "AGAGGCAACC.CCATCATTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400160",
#     #                                 "rgsm": "L2400160",
#     #                                 "rglb": "L2400160",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBKCATYSFY40BRX6WJWX",
#     #                         "libraryId": "L2400161",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CCATCATTAG.AGAGGCAACC.1.240229_A00130_0288_BH5HM2DSXC.L2400161",
#     #                                 "rgsm": "L2400161",
#     #                                 "rglb": "L2400161",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBN6EAXW4AXG7TQ1H6NC",
#     #                         "libraryId": "L2400162",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GATAGGCCGA.GCCATGTGCG.1.240229_A00130_0288_BH5HM2DSXC.L2400162",
#     #                                 "rgsm": "L2400162",
#     #                                 "rglb": "L2400162",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBQFX8V1QRW7KAV3MD1W",
#     #                         "libraryId": "L2400163",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ATGGTTGACT.AGGACAGGCC.1.240229_A00130_0288_BH5HM2DSXC.L2400163",
#     #                                 "rgsm": "L2400163",
#     #                                 "rglb": "L2400163",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBS64DNTHK6CE850CCNZ",
#     #                         "libraryId": "L2400164",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TATTGCGCTC.CCTAACACAG.1.240229_A00130_0288_BH5HM2DSXC.L2400164",
#     #                                 "rgsm": "L2400164",
#     #                                 "rglb": "L2400164",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBTZRYQNTGAHPC2T601D",
#     #                         "libraryId": "L2400165",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ACGCCTTGTT.ACGTTCCTTA.4.240229_A00130_0288_BH5HM2DSXC.L2400165",
#     #                                 "rgsm": "L2400165",
#     #                                 "rglb": "L2400165",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CBX10204CK7EKGTH9TMB",
#     #                         "libraryId": "L2400166",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TTCTACATAC.TTACAGTTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400166",
#     #                                 "rgsm": "L2400166",
#     #                                 "rglb": "L2400166",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "projectOwner": "VCCC",
#     #                 "projectName": "PO",
#     #                 "libraries": [
#     #                     {
#     #                         "orcabusId": "lib.01J5S9C4VMJ6PZ8GJ2G189AMXX",
#     #                         "libraryId": "L2400102",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GAATTCGT.TTATGAGT.1.240229_A00130_0288_BH5HM2DSXC.L2400102",
#     #                                 "rgsm": "L2400102",
#     #                                 "rglb": "L2400102",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "projectOwner": "UMCCR",
#     #                 "projectName": "Control",
#     #                 "libraries": [
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CGJ6G09YQ9KFHPSXMMVD",
#     #                         "libraryId": "L2400241",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GTTCCAAT.GCAGAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400241",
#     #                                 "rgsm": "L2400241",
#     #                                 "rglb": "L2400241",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CGKWDN7STKZKQM3KH9XR",
#     #                         "libraryId": "L2400242",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ACCTTGGC.ATGAGGCC.4.240229_A00130_0288_BH5HM2DSXC.L2400242",
#     #                                 "rgsm": "L2400242",
#     #                                 "rglb": "L2400242",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CH2SQ0P1SF7WAT5H4DSE",
#     #                         "libraryId": "L2400249",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "AGTTTCGA.CCTACGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400249",
#     #                                 "rgsm": "L2400249",
#     #                                 "rglb": "L2400249",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CHHNGFJN73NPRQMSYGN9",
#     #                         "libraryId": "L2400257",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GTGACGTT.TCCCAGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400257",
#     #                                 "rgsm": "L2400257",
#     #                                 "rglb": "L2400257",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "projectOwner": "TJohn",
#     #                 "projectName": "CAVATAK",
#     #                 "libraries": [
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CDF8HHG5PJE3ECJMKMY7",
#     #                         "libraryId": "L2400191",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GCACGGAC.TGCGAGAC.4.240229_A00130_0288_BH5HM2DSXC.L2400191",
#     #                                 "rgsm": "L2400191",
#     #                                 "rglb": "L2400191",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S",
#     #                         "libraryId": "L2400195",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ATGAGGCC.CAATTAAC.2.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                                 "rgsm": "L2400195",
#     #                                 "rglb": "L2400195",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "ATGAGGCC.CAATTAAC.3.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                                 "rgsm": "L2400195",
#     #                                 "rglb": "L2400195",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8",
#     #                         "libraryId": "L2400196",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ACTAAGAT.CCGCGGTT.2.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                                 "rgsm": "L2400196",
#     #                                 "rglb": "L2400196",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "ACTAAGAT.CCGCGGTT.3.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                                 "rgsm": "L2400196",
#     #                                 "rglb": "L2400196",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ",
#     #                         "libraryId": "L2400197",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GTCGGAGC.TTATAACC.2.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                                 "rgsm": "L2400197",
#     #                                 "rglb": "L2400197",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GTCGGAGC.TTATAACC.3.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                                 "rgsm": "L2400197",
#     #                                 "rglb": "L2400197",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GTCGGAGC.TTATAACC.4.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                                 "rgsm": "L2400197",
#     #                                 "rglb": "L2400197",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CDXCR7Q5K6A8VJRSMM4Q",
#     #                         "libraryId": "L2400198",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CTTGGTAT.GGACTTGG.4.240229_A00130_0288_BH5HM2DSXC.L2400198",
#     #                                 "rgsm": "L2400198",
#     #                                 "rglb": "L2400198",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "projectOwner": "Tothill",
#     #                 "projectName": "CUP",
#     #                 "libraries": [
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CFX5P69S4KZRQGDFKV1N",
#     #                         "libraryId": "L2400231",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TCGTAGTG.CCAAGTCT.2.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                                 "rgsm": "L2400231",
#     #                                 "rglb": "L2400231",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "TCGTAGTG.CCAAGTCT.3.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                                 "rgsm": "L2400231",
#     #                                 "rglb": "L2400231",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CGCAKQWHD9RBM9VXENY9",
#     #                         "libraryId": "L2400238",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GGAGCGTC.GCACGGAC.2.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                                 "rgsm": "L2400238",
#     #                                 "rglb": "L2400238",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GGAGCGTC.GCACGGAC.3.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                                 "rgsm": "L2400238",
#     #                                 "rglb": "L2400238",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CGEM1DHRQP72EP09B2TA",
#     #                         "libraryId": "L2400239",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ATGGCATG.GGTACCTT.2.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                                 "rgsm": "L2400239",
#     #                                 "rglb": "L2400239",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "ATGGCATG.GGTACCTT.3.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                                 "rgsm": "L2400239",
#     #                                 "rglb": "L2400239",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CGG9N9GH5879SY6A6BJB",
#     #                         "libraryId": "L2400240",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GCAATGCA.AACGTTCC.2.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                                 "rgsm": "L2400240",
#     #                                 "rglb": "L2400240",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GCAATGCA.AACGTTCC.3.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                                 "rgsm": "L2400240",
#     #                                 "rglb": "L2400240",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CHE4ERQ4H209DH397W8A",
#     #                         "libraryId": "L2400255",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GATCCGGG.AAGCAGGT.4.240229_A00130_0288_BH5HM2DSXC.L2400255",
#     #                                 "rgsm": "L2400255",
#     #                                 "rglb": "L2400255",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CHFXPDGYQ8TXHRWQR3PY",
#     #                         "libraryId": "L2400256",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "AACACCTG.CGCATGGG.4.240229_A00130_0288_BH5HM2DSXC.L2400256",
#     #                                 "rgsm": "L2400256",
#     #                                 "rglb": "L2400256",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "projectOwner": "Whittle",
#     #                 "projectName": "BPOP-retro",
#     #                 "libraries": [
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CH4CYPA4SP05H8KRX4W9",
#     #                         "libraryId": "L2400250",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GAACCTCT.GTCTGCGC.4.240229_A00130_0288_BH5HM2DSXC.L2400250",
#     #                                 "rgsm": "L2400250",
#     #                                 "rglb": "L2400250",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CH65E4EE5QJEJ1C60GGG",
#     #                         "libraryId": "L2400251",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GCCCAGTG.CCGCAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400251",
#     #                                 "rgsm": "L2400251",
#     #                                 "rglb": "L2400251",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CH7TGZMV39Z59WJ8H5GP",
#     #                         "libraryId": "L2400252",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TGACAGCT.CCCGTAGG.4.240229_A00130_0288_BH5HM2DSXC.L2400252",
#     #                                 "rgsm": "L2400252",
#     #                                 "rglb": "L2400252",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CH9TGMT2TJGBZX5VXHJY",
#     #                         "libraryId": "L2400253",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CATCACCC.ATATAGCA.4.240229_A00130_0288_BH5HM2DSXC.L2400253",
#     #                                 "rgsm": "L2400253",
#     #                                 "rglb": "L2400253",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "orcabusId": "lib.01J5S9CHBGAP2XSN4TG8SAMRYY",
#     #                         "libraryId": "L2400254",
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254",
#     #                                 "rgsm": "L2400254",
#     #                                 "rglb": "L2400254",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         }
#     #     ],
#     #     "fastq_list_rows_event_data_list": [
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GAATTCGT.TTATGAGT.1.240229_A00130_0288_BH5HM2DSXC.L2400102",
#     #                 "rgsm": "L2400102",
#     #                 "rglb": "L2400102",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400102",
#     #                 "orcabusId": "lib.01J5S9C4VMJ6PZ8GJ2G189AMXX"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GAGAATGGTT.TTGCTGCCGA.1.240229_A00130_0288_BH5HM2DSXC.L2400159",
#     #                 "rgsm": "L2400159",
#     #                 "rglb": "L2400159",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400159",
#     #                 "orcabusId": "lib.01J5S9CBG0NF8QBNVKM6ESCD60"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "AGAGGCAACC.CCATCATTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400160",
#     #                 "rgsm": "L2400160",
#     #                 "rglb": "L2400160",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400160",
#     #                 "orcabusId": "lib.01J5S9CBHP6NSB42RVFAP9PGJP"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "CCATCATTAG.AGAGGCAACC.1.240229_A00130_0288_BH5HM2DSXC.L2400161",
#     #                 "rgsm": "L2400161",
#     #                 "rglb": "L2400161",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400161",
#     #                 "orcabusId": "lib.01J5S9CBKCATYSFY40BRX6WJWX"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GATAGGCCGA.GCCATGTGCG.1.240229_A00130_0288_BH5HM2DSXC.L2400162",
#     #                 "rgsm": "L2400162",
#     #                 "rglb": "L2400162",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400162",
#     #                 "orcabusId": "lib.01J5S9CBN6EAXW4AXG7TQ1H6NC"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ATGGTTGACT.AGGACAGGCC.1.240229_A00130_0288_BH5HM2DSXC.L2400163",
#     #                 "rgsm": "L2400163",
#     #                 "rglb": "L2400163",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400163",
#     #                 "orcabusId": "lib.01J5S9CBQFX8V1QRW7KAV3MD1W"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "TATTGCGCTC.CCTAACACAG.1.240229_A00130_0288_BH5HM2DSXC.L2400164",
#     #                 "rgsm": "L2400164",
#     #                 "rglb": "L2400164",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400164",
#     #                 "orcabusId": "lib.01J5S9CBS64DNTHK6CE850CCNZ"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "TTCTACATAC.TTACAGTTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400166",
#     #                 "rgsm": "L2400166",
#     #                 "rglb": "L2400166",
#     #                 "lane": 1,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400166",
#     #                 "orcabusId": "lib.01J5S9CBX10204CK7EKGTH9TMB"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ATGAGGCC.CAATTAAC.2.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                 "rgsm": "L2400195",
#     #                 "rglb": "L2400195",
#     #                 "lane": 2,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400195",
#     #                 "orcabusId": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ACTAAGAT.CCGCGGTT.2.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                 "rgsm": "L2400196",
#     #                 "rglb": "L2400196",
#     #                 "lane": 2,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400196",
#     #                 "orcabusId": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GTCGGAGC.TTATAACC.2.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                 "rgsm": "L2400197",
#     #                 "rglb": "L2400197",
#     #                 "lane": 2,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400197",
#     #                 "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "TCGTAGTG.CCAAGTCT.2.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                 "rgsm": "L2400231",
#     #                 "rglb": "L2400231",
#     #                 "lane": 2,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400231",
#     #                 "orcabusId": "lib.01J5S9CFX5P69S4KZRQGDFKV1N"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GGAGCGTC.GCACGGAC.2.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                 "rgsm": "L2400238",
#     #                 "rglb": "L2400238",
#     #                 "lane": 2,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400238",
#     #                 "orcabusId": "lib.01J5S9CGCAKQWHD9RBM9VXENY9"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ATGGCATG.GGTACCTT.2.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                 "rgsm": "L2400239",
#     #                 "rglb": "L2400239",
#     #                 "lane": 2,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400239",
#     #                 "orcabusId": "lib.01J5S9CGEM1DHRQP72EP09B2TA"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GCAATGCA.AACGTTCC.2.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                 "rgsm": "L2400240",
#     #                 "rglb": "L2400240",
#     #                 "lane": 2,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400240",
#     #                 "orcabusId": "lib.01J5S9CGG9N9GH5879SY6A6BJB"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ATGAGGCC.CAATTAAC.3.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                 "rgsm": "L2400195",
#     #                 "rglb": "L2400195",
#     #                 "lane": 3,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400195",
#     #                 "orcabusId": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ACTAAGAT.CCGCGGTT.3.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                 "rgsm": "L2400196",
#     #                 "rglb": "L2400196",
#     #                 "lane": 3,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400196",
#     #                 "orcabusId": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GTCGGAGC.TTATAACC.3.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                 "rgsm": "L2400197",
#     #                 "rglb": "L2400197",
#     #                 "lane": 3,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400197",
#     #                 "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "TCGTAGTG.CCAAGTCT.3.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                 "rgsm": "L2400231",
#     #                 "rglb": "L2400231",
#     #                 "lane": 3,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400231",
#     #                 "orcabusId": "lib.01J5S9CFX5P69S4KZRQGDFKV1N"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GGAGCGTC.GCACGGAC.3.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                 "rgsm": "L2400238",
#     #                 "rglb": "L2400238",
#     #                 "lane": 3,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400238",
#     #                 "orcabusId": "lib.01J5S9CGCAKQWHD9RBM9VXENY9"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ATGGCATG.GGTACCTT.3.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                 "rgsm": "L2400239",
#     #                 "rglb": "L2400239",
#     #                 "lane": 3,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400239",
#     #                 "orcabusId": "lib.01J5S9CGEM1DHRQP72EP09B2TA"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GCAATGCA.AACGTTCC.3.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                 "rgsm": "L2400240",
#     #                 "rglb": "L2400240",
#     #                 "lane": 3,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400240",
#     #                 "orcabusId": "lib.01J5S9CGG9N9GH5879SY6A6BJB"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ACGCCTTGTT.ACGTTCCTTA.4.240229_A00130_0288_BH5HM2DSXC.L2400165",
#     #                 "rgsm": "L2400165",
#     #                 "rglb": "L2400165",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400165",
#     #                 "orcabusId": "lib.01J5S9CBTZRYQNTGAHPC2T601D"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GCACGGAC.TGCGAGAC.4.240229_A00130_0288_BH5HM2DSXC.L2400191",
#     #                 "rgsm": "L2400191",
#     #                 "rglb": "L2400191",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400191",
#     #                 "orcabusId": "lib.01J5S9CDF8HHG5PJE3ECJMKMY7"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GTCGGAGC.TTATAACC.4.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                 "rgsm": "L2400197",
#     #                 "rglb": "L2400197",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400197",
#     #                 "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "CTTGGTAT.GGACTTGG.4.240229_A00130_0288_BH5HM2DSXC.L2400198",
#     #                 "rgsm": "L2400198",
#     #                 "rglb": "L2400198",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400198",
#     #                 "orcabusId": "lib.01J5S9CDXCR7Q5K6A8VJRSMM4Q"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GTTCCAAT.GCAGAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400241",
#     #                 "rgsm": "L2400241",
#     #                 "rglb": "L2400241",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400241",
#     #                 "orcabusId": "lib.01J5S9CGJ6G09YQ9KFHPSXMMVD"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "ACCTTGGC.ATGAGGCC.4.240229_A00130_0288_BH5HM2DSXC.L2400242",
#     #                 "rgsm": "L2400242",
#     #                 "rglb": "L2400242",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400242",
#     #                 "orcabusId": "lib.01J5S9CGKWDN7STKZKQM3KH9XR"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "AGTTTCGA.CCTACGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400249",
#     #                 "rgsm": "L2400249",
#     #                 "rglb": "L2400249",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400249",
#     #                 "orcabusId": "lib.01J5S9CH2SQ0P1SF7WAT5H4DSE"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GAACCTCT.GTCTGCGC.4.240229_A00130_0288_BH5HM2DSXC.L2400250",
#     #                 "rgsm": "L2400250",
#     #                 "rglb": "L2400250",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400250",
#     #                 "orcabusId": "lib.01J5S9CH4CYPA4SP05H8KRX4W9"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GCCCAGTG.CCGCAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400251",
#     #                 "rgsm": "L2400251",
#     #                 "rglb": "L2400251",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400251",
#     #                 "orcabusId": "lib.01J5S9CH65E4EE5QJEJ1C60GGG"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "TGACAGCT.CCCGTAGG.4.240229_A00130_0288_BH5HM2DSXC.L2400252",
#     #                 "rgsm": "L2400252",
#     #                 "rglb": "L2400252",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400252",
#     #                 "orcabusId": "lib.01J5S9CH7TGZMV39Z59WJ8H5GP"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "CATCACCC.ATATAGCA.4.240229_A00130_0288_BH5HM2DSXC.L2400253",
#     #                 "rgsm": "L2400253",
#     #                 "rglb": "L2400253",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400253",
#     #                 "orcabusId": "lib.01J5S9CH9TGMT2TJGBZX5VXHJY"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254",
#     #                 "rgsm": "L2400254",
#     #                 "rglb": "L2400254",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400254",
#     #                 "orcabusId": "lib.01J5S9CHBGAP2XSN4TG8SAMRYY"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GATCCGGG.AAGCAGGT.4.240229_A00130_0288_BH5HM2DSXC.L2400255",
#     #                 "rgsm": "L2400255",
#     #                 "rglb": "L2400255",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400255",
#     #                 "orcabusId": "lib.01J5S9CHE4ERQ4H209DH397W8A"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "AACACCTG.CGCATGGG.4.240229_A00130_0288_BH5HM2DSXC.L2400256",
#     #                 "rgsm": "L2400256",
#     #                 "rglb": "L2400256",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400256",
#     #                 "orcabusId": "lib.01J5S9CHFXPDGYQ8TXHRWQR3PY"
#     #             }
#     #         },
#     #         {
#     #             "fastqListRow": {
#     #                 "rgid": "GTGACGTT.TCCCAGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400257",
#     #                 "rgsm": "L2400257",
#     #                 "rglb": "L2400257",
#     #                 "lane": 4,
#     #                 "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#     #             },
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400257",
#     #                 "orcabusId": "lib.01J5S9CHHNGFJN73NPRQMSYGN9"
#     #             }
#     #         }
#     #     ],
#     #     "complete_fastq_list_row_shower_event_data": {
#     #         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#     #     }
#     # }
