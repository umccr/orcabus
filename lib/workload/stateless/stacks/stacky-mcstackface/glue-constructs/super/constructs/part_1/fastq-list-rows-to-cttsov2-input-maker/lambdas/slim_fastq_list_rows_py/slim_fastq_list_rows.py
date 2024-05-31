#!/usr/bin/env python3

"""
Custom script for each library id, generate a samplesheet and fastq list row set

"""

from typing import List


def get_fastq_list_rows_for_library_id(library_id: str, fastq_list_rows: List):
    return list(
        filter(
            lambda fastq_list_row_iter: fastq_list_row_iter.get("RGSM") == library_id,
            fastq_list_rows
        )
    )


def handler(event, context):
    """
    Take in the fastq list rows, and samplesheet
    :param event:
    :param context:
    :return:
    """
    # Get the library id
    library_id = event.get("library_id")
    fastq_list_rows = event.get("fastq_list_rows")

    return {
        "fastq_list_rows": get_fastq_list_rows_for_library_id(library_id, fastq_list_rows),
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "library_id": "L2400162",
#                     "fastq_list_rows": [
#                         {
#                             "RGID": "GAATTCGT.TTATGAGT.1",
#                             "RGSM": "L2400102",
#                             "RGLB": "L2400102",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GAGAATGGTT.TTGCTGCCGA.1",
#                             "RGSM": "L2400159",
#                             "RGLB": "L2400159",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AGAGGCAACC.CCATCATTAG.1",
#                             "RGSM": "L2400160",
#                             "RGLB": "L2400160",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CCATCATTAG.AGAGGCAACC.1",
#                             "RGSM": "L2400161",
#                             "RGLB": "L2400161",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GATAGGCCGA.GCCATGTGCG.1",
#                             "RGSM": "L2400162",
#                             "RGLB": "L2400162",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGTTGACT.AGGACAGGCC.1",
#                             "RGSM": "L2400163",
#                             "RGLB": "L2400163",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TATTGCGCTC.CCTAACACAG.1",
#                             "RGSM": "L2400164",
#                             "RGLB": "L2400164",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TTCTACATAC.TTACAGTTAG.1",
#                             "RGSM": "L2400166",
#                             "RGLB": "L2400166",
#                             "Lane": 1,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGAGGCC.CAATTAAC.2",
#                             "RGSM": "L2400195",
#                             "RGLB": "L2400195",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACTAAGAT.CCGCGGTT.2",
#                             "RGSM": "L2400196",
#                             "RGLB": "L2400196",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.2",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TCGTAGTG.CCAAGTCT.2",
#                             "RGSM": "L2400231",
#                             "RGLB": "L2400231",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GGAGCGTC.GCACGGAC.2",
#                             "RGSM": "L2400238",
#                             "RGLB": "L2400238",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGCATG.GGTACCTT.2",
#                             "RGSM": "L2400239",
#                             "RGLB": "L2400239",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCAATGCA.AACGTTCC.2",
#                             "RGSM": "L2400240",
#                             "RGLB": "L2400240",
#                             "Lane": 2,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGAGGCC.CAATTAAC.3",
#                             "RGSM": "L2400195",
#                             "RGLB": "L2400195",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACTAAGAT.CCGCGGTT.3",
#                             "RGSM": "L2400196",
#                             "RGLB": "L2400196",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.3",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TCGTAGTG.CCAAGTCT.3",
#                             "RGSM": "L2400231",
#                             "RGLB": "L2400231",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GGAGCGTC.GCACGGAC.3",
#                             "RGSM": "L2400238",
#                             "RGLB": "L2400238",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ATGGCATG.GGTACCTT.3",
#                             "RGSM": "L2400239",
#                             "RGLB": "L2400239",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCAATGCA.AACGTTCC.3",
#                             "RGSM": "L2400240",
#                             "RGLB": "L2400240",
#                             "Lane": 3,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACGCCTTGTT.ACGTTCCTTA.4",
#                             "RGSM": "L2400165",
#                             "RGLB": "L2400165",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCACGGAC.TGCGAGAC.4",
#                             "RGSM": "L2400191",
#                             "RGLB": "L2400191",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTCGGAGC.TTATAACC.4",
#                             "RGSM": "L2400197",
#                             "RGLB": "L2400197",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CTTGGTAT.GGACTTGG.4",
#                             "RGSM": "L2400198",
#                             "RGLB": "L2400198",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTTCCAAT.GCAGAATT.4",
#                             "RGSM": "L2400241",
#                             "RGLB": "L2400241",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "ACCTTGGC.ATGAGGCC.4",
#                             "RGSM": "L2400242",
#                             "RGLB": "L2400242",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AGTTTCGA.CCTACGAT.4",
#                             "RGSM": "L2400249",
#                             "RGLB": "L2400249",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GAACCTCT.GTCTGCGC.4",
#                             "RGSM": "L2400250",
#                             "RGLB": "L2400250",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GCCCAGTG.CCGCAATT.4",
#                             "RGSM": "L2400251",
#                             "RGLB": "L2400251",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "TGACAGCT.CCCGTAGG.4",
#                             "RGSM": "L2400252",
#                             "RGLB": "L2400252",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CATCACCC.ATATAGCA.4",
#                             "RGSM": "L2400253",
#                             "RGLB": "L2400253",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "CTGGAGTA.GTTCGGTT.4",
#                             "RGSM": "L2400254",
#                             "RGLB": "L2400254",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GATCCGGG.AAGCAGGT.4",
#                             "RGSM": "L2400255",
#                             "RGLB": "L2400255",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "AACACCTG.CGCATGGG.4",
#                             "RGSM": "L2400256",
#                             "RGLB": "L2400256",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "RGID": "GTGACGTT.TCCCAGAT.4",
#                             "RGSM": "L2400257",
#                             "RGLB": "L2400257",
#                             "Lane": 4,
#                             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#                             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#                         }
#                     ]
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "fastq_list_rows": [
#     #     {
#     #       "RGID": "GATAGGCCGA.GCCATGTGCG.1",
#     #       "RGSM": "L2400162",
#     #       "RGLB": "L2400162",
#     #       "Lane": 1,
#     #       "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#     #       "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#     #     }
#     #   ]
#     # }
