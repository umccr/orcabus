#!/usr/bin/env python3

"""
Custom script for each library id, generate a samplesheet and fastq list row set

"""

from typing import Dict


def get_samplesheet_for_tso500_library(library_id: str, samplesheet: Dict):
    return {
        "header": samplesheet.get("header"),
        "reads": samplesheet.get("reads"),
        "bclconvert_settings": {
            "adapter_read_1": "CTGTCTCTTATACACATCT",
            "adapter_read_2": "CTGTCTCTTATACACATCT",
            "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
            "mask_short_reads": 35,
            "adapter_behavior": "trim",
            "minimum_trimmed_read_length": 35
        },
        "bclconvert_data": list(
            filter(
                lambda library_id_iter: library_id_iter.get("sample_id") == library_id,
                samplesheet.get("bclconvert_data")
            )
        ),
        "tso500l_settings": {
            "adapter_read_1": "CTGTCTCTTATACACATCT",
            "adapter_read_2": "CTGTCTCTTATACACATCT",
            "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
            "mask_short_reads": 35,
            "adapter_behavior": "trim",
            "minimum_trimmed_read_length": 35
        },
        "tso500l_data": list(
            filter(
                lambda library_id_iter: library_id_iter.get("sample_id") == library_id,
                samplesheet.get("tso500l_data")
            )
        )
    }


def get_fastq_list_rows_for_library_id(library_id: str, fastq_list_rows: Dict):
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
    samplesheet = event.get("samplesheet")

    # Get tso500 library ids
    tso500l_library_ids = list(
        set(
            list(
                map(
                    lambda tso500l_data_iter: tso500l_data_iter.get("sample_id"),
                    samplesheet.get("tso500l_data")
                )
            )
        )
    )

    return {
        "library_id_map": tso500l_library_ids
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "samplesheet": {
#                         "header": {
#                             "file_format_version": 2,
#                             "run_name": "Tsqn240214-26-ctTSOv2_29Feb24",
#                             "instrument_type": "NovaSeq"
#                         },
#                         "reads": {
#                             "read_1_cycles": 151,
#                             "read_2_cycles": 151,
#                             "index_1_cycles": 10,
#                             "index_2_cycles": 10
#                         },
#                         "bclconvert_settings": {
#                             "minimum_trimmed_read_length": 35,
#                             "minimum_adapter_overlap": 3,
#                             "mask_short_reads": 35,
#                             "software_version": "4.2.7"
#                         },
#                         "bclconvert_data": [
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400102",
#                                 "index": "GAATTCGT",
#                                 "index2": "TTATGAGT",
#                                 "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
#                             },
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400159",
#                                 "index": "GAGAATGGTT",
#                                 "index2": "TTGCTGCCGA",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400160",
#                                 "index": "AGAGGCAACC",
#                                 "index2": "CCATCATTAG",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400161",
#                                 "index": "CCATCATTAG",
#                                 "index2": "AGAGGCAACC",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400162",
#                                 "index": "GATAGGCCGA",
#                                 "index2": "GCCATGTGCG",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400163",
#                                 "index": "ATGGTTGACT",
#                                 "index2": "AGGACAGGCC",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400164",
#                                 "index": "TATTGCGCTC",
#                                 "index2": "CCTAACACAG",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 1,
#                                 "sample_id": "L2400166",
#                                 "index": "TTCTACATAC",
#                                 "index2": "TTACAGTTAG",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 2,
#                                 "sample_id": "L2400195",
#                                 "index": "ATGAGGCC",
#                                 "index2": "CAATTAAC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 2,
#                                 "sample_id": "L2400196",
#                                 "index": "ACTAAGAT",
#                                 "index2": "CCGCGGTT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 2,
#                                 "sample_id": "L2400197",
#                                 "index": "GTCGGAGC",
#                                 "index2": "TTATAACC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 2,
#                                 "sample_id": "L2400231",
#                                 "index": "TCGTAGTG",
#                                 "index2": "CCAAGTCT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 2,
#                                 "sample_id": "L2400238",
#                                 "index": "GGAGCGTC",
#                                 "index2": "GCACGGAC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 2,
#                                 "sample_id": "L2400239",
#                                 "index": "ATGGCATG",
#                                 "index2": "GGTACCTT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 2,
#                                 "sample_id": "L2400240",
#                                 "index": "GCAATGCA",
#                                 "index2": "AACGTTCC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 3,
#                                 "sample_id": "L2400195",
#                                 "index": "ATGAGGCC",
#                                 "index2": "CAATTAAC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 3,
#                                 "sample_id": "L2400196",
#                                 "index": "ACTAAGAT",
#                                 "index2": "CCGCGGTT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 3,
#                                 "sample_id": "L2400197",
#                                 "index": "GTCGGAGC",
#                                 "index2": "TTATAACC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 3,
#                                 "sample_id": "L2400231",
#                                 "index": "TCGTAGTG",
#                                 "index2": "CCAAGTCT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 3,
#                                 "sample_id": "L2400238",
#                                 "index": "GGAGCGTC",
#                                 "index2": "GCACGGAC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 3,
#                                 "sample_id": "L2400239",
#                                 "index": "ATGGCATG",
#                                 "index2": "GGTACCTT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 3,
#                                 "sample_id": "L2400240",
#                                 "index": "GCAATGCA",
#                                 "index2": "AACGTTCC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400165",
#                                 "index": "ACGCCTTGTT",
#                                 "index2": "ACGTTCCTTA",
#                                 "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                 "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                 "adapter_read_2": "CTGTCTCTTATACACATCT"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400191",
#                                 "index": "GCACGGAC",
#                                 "index2": "TGCGAGAC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400197",
#                                 "index": "GTCGGAGC",
#                                 "index2": "TTATAACC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400198",
#                                 "index": "CTTGGTAT",
#                                 "index2": "GGACTTGG",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400241",
#                                 "index": "GTTCCAAT",
#                                 "index2": "GCAGAATT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400242",
#                                 "index": "ACCTTGGC",
#                                 "index2": "ATGAGGCC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400249",
#                                 "index": "AGTTTCGA",
#                                 "index2": "CCTACGAT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400250",
#                                 "index": "GAACCTCT",
#                                 "index2": "GTCTGCGC",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400251",
#                                 "index": "GCCCAGTG",
#                                 "index2": "CCGCAATT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400252",
#                                 "index": "TGACAGCT",
#                                 "index2": "CCCGTAGG",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400253",
#                                 "index": "CATCACCC",
#                                 "index2": "ATATAGCA",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400254",
#                                 "index": "CTGGAGTA",
#                                 "index2": "GTTCGGTT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400255",
#                                 "index": "GATCCGGG",
#                                 "index2": "AAGCAGGT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400256",
#                                 "index": "AACACCTG",
#                                 "index2": "CGCATGGG",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             },
#                             {
#                                 "lane": 4,
#                                 "sample_id": "L2400257",
#                                 "index": "GTGACGTT",
#                                 "index2": "TCCCAGAT",
#                                 "override_cycles": "Y151;I8N2;I8N2;Y151"
#                             }
#                         ],
#                         "cloud_settings": {
#                             "generated_version": "0.0.0",
#                             "cloud_workflow": "ica_workflow_1",
#                             "bclconvert_pipeline": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7"
#                         },
#                         "cloud_data": [
#                             {
#                                 "sample_id": "L2400102",
#                                 "library_name": "L2400102_GAATTCGT_TTATGAGT",
#                                 "library_prep_kit_name": "ctTSO"
#                             },
#                             {
#                                 "sample_id": "L2400159",
#                                 "library_name": "L2400159_GAGAATGGTT_TTGCTGCCGA",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400160",
#                                 "library_name": "L2400160_AGAGGCAACC_CCATCATTAG",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400161",
#                                 "library_name": "L2400161_CCATCATTAG_AGAGGCAACC",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400162",
#                                 "library_name": "L2400162_GATAGGCCGA_GCCATGTGCG",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400163",
#                                 "library_name": "L2400163_ATGGTTGACT_AGGACAGGCC",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400164",
#                                 "library_name": "L2400164_TATTGCGCTC_CCTAACACAG",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400165",
#                                 "library_name": "L2400165_ACGCCTTGTT_ACGTTCCTTA",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400166",
#                                 "library_name": "L2400166_TTCTACATAC_TTACAGTTAG",
#                                 "library_prep_kit_name": "ctTSOv2"
#                             },
#                             {
#                                 "sample_id": "L2400191",
#                                 "library_name": "L2400191_GCACGGAC_TGCGAGAC",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400195",
#                                 "library_name": "L2400195_ATGAGGCC_CAATTAAC",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400196",
#                                 "library_name": "L2400196_ACTAAGAT_CCGCGGTT",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400197",
#                                 "library_name": "L2400197_GTCGGAGC_TTATAACC",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400198",
#                                 "library_name": "L2400198_CTTGGTAT_GGACTTGG",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400231",
#                                 "library_name": "L2400231_TCGTAGTG_CCAAGTCT",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400238",
#                                 "library_name": "L2400238_GGAGCGTC_GCACGGAC",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400239",
#                                 "library_name": "L2400239_ATGGCATG_GGTACCTT",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400240",
#                                 "library_name": "L2400240_GCAATGCA_AACGTTCC",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400241",
#                                 "library_name": "L2400241_GTTCCAAT_GCAGAATT",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400242",
#                                 "library_name": "L2400242_ACCTTGGC_ATGAGGCC",
#                                 "library_prep_kit_name": "TsqNano"
#                             },
#                             {
#                                 "sample_id": "L2400249",
#                                 "library_name": "L2400249_AGTTTCGA_CCTACGAT",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400250",
#                                 "library_name": "L2400250_GAACCTCT_GTCTGCGC",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400251",
#                                 "library_name": "L2400251_GCCCAGTG_CCGCAATT",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400252",
#                                 "library_name": "L2400252_TGACAGCT_CCCGTAGG",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400253",
#                                 "library_name": "L2400253_CATCACCC_ATATAGCA",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400254",
#                                 "library_name": "L2400254_CTGGAGTA_GTTCGGTT",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400255",
#                                 "library_name": "L2400255_GATCCGGG_AAGCAGGT",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400256",
#                                 "library_name": "L2400256_AACACCTG_CGCATGGG",
#                                 "library_prep_kit_name": "NebRNA"
#                             },
#                             {
#                                 "sample_id": "L2400257",
#                                 "library_name": "L2400257_GTGACGTT_TCCCAGAT",
#                                 "library_prep_kit_name": "NebRNA"
#                             }
#                         ],
#                         "tso500l_settings": {
#                             "adapter_read_1": "CTGTCTCTTATACACATCT",
#                             "adapter_read_2": "CTGTCTCTTATACACATCT",
#                             "adapter_behaviour": "trim",
#                             "minimum_trimmed_read_length": 35,
#                             "mask_short_reads": 35,
#                             "override_cycles": "U7N1Y143;I10;I10;U7N1Y143"
#                         },
#                         "tso500l_data": [
#                             {
#                                 "sample_id": "L2400159",
#                                 "sample_type": "DNA",
#                                 "lane": 1,
#                                 "index": "GAGAATGGTT",
#                                 "index2": "TTGCTGCCGA",
#                                 "i7_index_id": "UDP0017",
#                                 "i5_index_id": "UDP0017"
#                             },
#                             {
#                                 "sample_id": "L2400160",
#                                 "sample_type": "DNA",
#                                 "lane": 1,
#                                 "index": "AGAGGCAACC",
#                                 "index2": "CCATCATTAG",
#                                 "i7_index_id": "UDP0018",
#                                 "i5_index_id": "UDP0018"
#                             },
#                             {
#                                 "sample_id": "L2400161",
#                                 "sample_type": "DNA",
#                                 "lane": 1,
#                                 "index": "CCATCATTAG",
#                                 "index2": "AGAGGCAACC",
#                                 "i7_index_id": "UDP0019",
#                                 "i5_index_id": "UDP0019"
#                             },
#                             {
#                                 "sample_id": "L2400162",
#                                 "sample_type": "DNA",
#                                 "lane": 1,
#                                 "index": "GATAGGCCGA",
#                                 "index2": "GCCATGTGCG",
#                                 "i7_index_id": "UDP0020",
#                                 "i5_index_id": "UDP0020"
#                             },
#                             {
#                                 "sample_id": "L2400163",
#                                 "sample_type": "DNA",
#                                 "lane": 1,
#                                 "index": "ATGGTTGACT",
#                                 "index2": "AGGACAGGCC",
#                                 "i7_index_id": "UDP0021",
#                                 "i5_index_id": "UDP0021"
#                             },
#                             {
#                                 "sample_id": "L2400164",
#                                 "sample_type": "DNA",
#                                 "lane": 1,
#                                 "index": "TATTGCGCTC",
#                                 "index2": "CCTAACACAG",
#                                 "i7_index_id": "UDP0022",
#                                 "i5_index_id": "UDP0022"
#                             },
#                             {
#                                 "sample_id": "L2400165",
#                                 "sample_type": "DNA",
#                                 "lane": 4,
#                                 "index": "ACGCCTTGTT",
#                                 "index2": "ACGTTCCTTA",
#                                 "i7_index_id": "UDP0023",
#                                 "i5_index_id": "UDP0023"
#                             },
#                             {
#                                 "sample_id": "L2400166",
#                                 "sample_type": "DNA",
#                                 "lane": 1,
#                                 "index": "TTCTACATAC",
#                                 "index2": "TTACAGTTAG",
#                                 "i7_index_id": "UDP0024",
#                                 "i5_index_id": "UDP0024"
#                             }
#                         ]
#                     }
#                 }
#                 ,
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "library_id_map": [
#     #     "L2400161",
#     #     "L2400166",
#     #     "L2400164",
#     #     "L2400159",
#     #     "L2400162",
#     #     "L2400160",
#     #     "L2400165",
#     #     "L2400163"
#     #   ]
#     # }
