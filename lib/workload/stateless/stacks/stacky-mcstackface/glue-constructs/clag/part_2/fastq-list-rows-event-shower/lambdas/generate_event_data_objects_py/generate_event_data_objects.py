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


def generate_fastq_list_row_event(fastq_list_row: Dict) -> Dict:
    """
    Generate the fastq list row event

    :param fastq_list_row:
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

    return new_fastq_list_row_dict


def handler(event, context):
    """
    Given a set of fastq list rows (and instrument run id), generate a set of event maps for each fastq file.
    :param event:
    :param context:
    :return:
    """

    # Get the fastq list rows and instrument run id
    fastq_list_rows = event['fastq_list_rows']
    instrument_run_id = event['instrument_run_id']

    # Generate the fastq list row events
    fastq_list_row_event_data_list = list(
        map(
            generate_fastq_list_row_event,
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

    # Return the event data
    return {
        "start_fastq_list_row_shower_event_data": start_fastq_list_row_shower_event_data,
        "complete_fastq_list_row_shower_event_data": complete_fastq_list_row_shower_event_data,
        "fastq_list_rows_event_data_list": fastq_list_row_event_data_list
    }


# Test the function
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
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GAGAATGGTT.TTGCTGCCGA.1",
#                             "RGSM": "L2400159",
#                             "RGLB": "L2400159",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AGAGGCAACC.CCATCATTAG.1",
#                             "RGSM": "L2400160",
#                             "RGLB": "L2400160",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CCATCATTAG.AGAGGCAACC.1",
#                             "RGSM": "L2400161",
#                             "RGLB": "L2400161",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GATAGGCCGA.GCCATGTGCG.1",
#                             "RGSM": "L2400162",
#                             "RGLB": "L2400162",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGTTGACT.AGGACAGGCC.1",
#                             "RGSM": "L2400163",
#                             "RGLB": "L2400163",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TATTGCGCTC.CCTAACACAG.1",
#                             "RGSM": "L2400164",
#                             "RGLB": "L2400164",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TTCTACATAC.TTACAGTTAG.1",
#                             "RGSM": "L2400166",
#                             "RGLB": "L2400166",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGAGGCC.CAATTAAC.2",
#                             "RGSM": "L2400195",
#                             "RGLB": "L2400195",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACTAAGAT.CCGCGGTT.2",
#                             "RGSM": "L2400196",
#                             "RGLB": "L2400196",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.2",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TCGTAGTG.CCAAGTCT.2",
#                             "RGSM": "L2400231",
#                             "RGLB": "L2400231",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GGAGCGTC.GCACGGAC.2",
#                             "RGSM": "L2400238",
#                             "RGLB": "L2400238",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGCATG.GGTACCTT.2",
#                             "RGSM": "L2400239",
#                             "RGLB": "L2400239",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCAATGCA.AACGTTCC.2",
#                             "RGSM": "L2400240",
#                             "RGLB": "L2400240",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGAGGCC.CAATTAAC.3",
#                             "RGSM": "L2400195",
#                             "RGLB": "L2400195",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACTAAGAT.CCGCGGTT.3",
#                             "RGSM": "L2400196",
#                             "RGLB": "L2400196",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.3",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TCGTAGTG.CCAAGTCT.3",
#                             "RGSM": "L2400231",
#                             "RGLB": "L2400231",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GGAGCGTC.GCACGGAC.3",
#                             "RGSM": "L2400238",
#                             "RGLB": "L2400238",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGCATG.GGTACCTT.3",
#                             "RGSM": "L2400239",
#                             "RGLB": "L2400239",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCAATGCA.AACGTTCC.3",
#                             "RGSM": "L2400240",
#                             "RGLB": "L2400240",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACGCCTTGTT.ACGTTCCTTA.4",
#                             "RGSM": "L2400165",
#                             "RGLB": "L2400165",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCACGGAC.TGCGAGAC.4",
#                             "RGSM": "L2400191",
#                             "RGLB": "L2400191",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.4",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CTTGGTAT.GGACTTGG.4",
#                             "RGSM": "L2400198",
#                             "RGLB": "L2400198",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTTCCAAT.GCAGAATT.4",
#                             "RGSM": "L2400241",
#                             "RGLB": "L2400241",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACCTTGGC.ATGAGGCC.4",
#                             "RGSM": "L2400242",
#                             "RGLB": "L2400242",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AGTTTCGA.CCTACGAT.4",
#                             "RGSM": "L2400249",
#                             "RGLB": "L2400249",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GAACCTCT.GTCTGCGC.4",
#                             "RGSM": "L2400250",
#                             "RGLB": "L2400250",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCCCAGTG.CCGCAATT.4",
#                             "RGSM": "L2400251",
#                             "RGLB": "L2400251",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TGACAGCT.CCCGTAGG.4",
#                             "RGSM": "L2400252",
#                             "RGLB": "L2400252",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CATCACCC.ATATAGCA.4",
#                             "RGSM": "L2400253",
#                             "RGLB": "L2400253",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CTGGAGTA.GTTCGGTT.4",
#                             "RGSM": "L2400254",
#                             "RGLB": "L2400254",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GATCCGGG.AAGCAGGT.4",
#                             "RGSM": "L2400255",
#                             "RGLB": "L2400255",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AACACCTG.CGCATGGG.4",
#                             "RGSM": "L2400256",
#                             "RGLB": "L2400256",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTGACGTT.TCCCAGAT.4",
#                             "RGSM": "L2400257",
#                             "RGLB": "L2400257",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#                         }
#                     ]
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
#     #     "complete_fastq_list_row_shower_event_data": {
#     #         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#     #     },
#     #     "fastq_list_rows_event_data_list": [
#     #         {
#     #             "rgid": "GAATTCGT.TTATGAGT.1",
#     #             "rgsm": "L2400102",
#     #             "rglb": "L2400102",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GAGAATGGTT.TTGCTGCCGA.1",
#     #             "rgsm": "L2400159",
#     #             "rglb": "L2400159",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "AGAGGCAACC.CCATCATTAG.1",
#     #             "rgsm": "L2400160",
#     #             "rglb": "L2400160",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "CCATCATTAG.AGAGGCAACC.1",
#     #             "rgsm": "L2400161",
#     #             "rglb": "L2400161",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GATAGGCCGA.GCCATGTGCG.1",
#     #             "rgsm": "L2400162",
#     #             "rglb": "L2400162",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ATGGTTGACT.AGGACAGGCC.1",
#     #             "rgsm": "L2400163",
#     #             "rglb": "L2400163",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "TATTGCGCTC.CCTAACACAG.1",
#     #             "rgsm": "L2400164",
#     #             "rglb": "L2400164",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "TTCTACATAC.TTACAGTTAG.1",
#     #             "rgsm": "L2400166",
#     #             "rglb": "L2400166",
#     #             "lane": 1,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ATGAGGCC.CAATTAAC.2",
#     #             "rgsm": "L2400195",
#     #             "rglb": "L2400195",
#     #             "lane": 2,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ACTAAGAT.CCGCGGTT.2",
#     #             "rgsm": "L2400196",
#     #             "rglb": "L2400196",
#     #             "lane": 2,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GTCGGAGC.TTATAACC.2",
#     #             "rgsm": "L2400197",
#     #             "rglb": "L2400197",
#     #             "lane": 2,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "TCGTAGTG.CCAAGTCT.2",
#     #             "rgsm": "L2400231",
#     #             "rglb": "L2400231",
#     #             "lane": 2,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GGAGCGTC.GCACGGAC.2",
#     #             "rgsm": "L2400238",
#     #             "rglb": "L2400238",
#     #             "lane": 2,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ATGGCATG.GGTACCTT.2",
#     #             "rgsm": "L2400239",
#     #             "rglb": "L2400239",
#     #             "lane": 2,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GCAATGCA.AACGTTCC.2",
#     #             "rgsm": "L2400240",
#     #             "rglb": "L2400240",
#     #             "lane": 2,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ATGAGGCC.CAATTAAC.3",
#     #             "rgsm": "L2400195",
#     #             "rglb": "L2400195",
#     #             "lane": 3,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ACTAAGAT.CCGCGGTT.3",
#     #             "rgsm": "L2400196",
#     #             "rglb": "L2400196",
#     #             "lane": 3,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GTCGGAGC.TTATAACC.3",
#     #             "rgsm": "L2400197",
#     #             "rglb": "L2400197",
#     #             "lane": 3,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "TCGTAGTG.CCAAGTCT.3",
#     #             "rgsm": "L2400231",
#     #             "rglb": "L2400231",
#     #             "lane": 3,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GGAGCGTC.GCACGGAC.3",
#     #             "rgsm": "L2400238",
#     #             "rglb": "L2400238",
#     #             "lane": 3,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ATGGCATG.GGTACCTT.3",
#     #             "rgsm": "L2400239",
#     #             "rglb": "L2400239",
#     #             "lane": 3,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GCAATGCA.AACGTTCC.3",
#     #             "rgsm": "L2400240",
#     #             "rglb": "L2400240",
#     #             "lane": 3,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ACGCCTTGTT.ACGTTCCTTA.4",
#     #             "rgsm": "L2400165",
#     #             "rglb": "L2400165",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GCACGGAC.TGCGAGAC.4",
#     #             "rgsm": "L2400191",
#     #             "rglb": "L2400191",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GTCGGAGC.TTATAACC.4",
#     #             "rgsm": "L2400197",
#     #             "rglb": "L2400197",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "CTTGGTAT.GGACTTGG.4",
#     #             "rgsm": "L2400198",
#     #             "rglb": "L2400198",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GTTCCAAT.GCAGAATT.4",
#     #             "rgsm": "L2400241",
#     #             "rglb": "L2400241",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "ACCTTGGC.ATGAGGCC.4",
#     #             "rgsm": "L2400242",
#     #             "rglb": "L2400242",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "AGTTTCGA.CCTACGAT.4",
#     #             "rgsm": "L2400249",
#     #             "rglb": "L2400249",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GAACCTCT.GTCTGCGC.4",
#     #             "rgsm": "L2400250",
#     #             "rglb": "L2400250",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GCCCAGTG.CCGCAATT.4",
#     #             "rgsm": "L2400251",
#     #             "rglb": "L2400251",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "TGACAGCT.CCCGTAGG.4",
#     #             "rgsm": "L2400252",
#     #             "rglb": "L2400252",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "CATCACCC.ATATAGCA.4",
#     #             "rgsm": "L2400253",
#     #             "rglb": "L2400253",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "CTGGAGTA.GTTCGGTT.4",
#     #             "rgsm": "L2400254",
#     #             "rglb": "L2400254",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GATCCGGG.AAGCAGGT.4",
#     #             "rgsm": "L2400255",
#     #             "rglb": "L2400255",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "AACACCTG.CGCATGGG.4",
#     #             "rgsm": "L2400256",
#     #             "rglb": "L2400256",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "rgid": "GTGACGTT.TCCCAGAT.4",
#     #             "rgsm": "L2400257",
#     #             "rglb": "L2400257",
#     #             "lane": 4,
#     #             "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#     #             "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/20240621fe580652/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#     #         }
#     #     ]
#     # }
