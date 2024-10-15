#!/usr/bin/env python3

"""
Get Library Objects from samplesheet
"""

# Standard imports
import logging
from typing import List, Dict

# Layer imports
from metadata_tools import get_all_libraries

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_library_objs(library_id_list: List[str]) -> List[Dict]:
    """
    Get all libraries by doing a bulk download rather than query 1-1
    :param library_id_list:
    :return:
    """
    # Get just the relevant libraries
    return sorted(
        filter(
            lambda library_obj_iter: library_obj_iter['libraryId'] in library_id_list,
            get_all_libraries()
        ),
        key=lambda element_iter: element_iter.get("orcabusId")
    )


def handler(event, context):
    """
    Given a samplesheet dictionary, collect the sample_id attributes as library ids.

    For each unique library id, return the library object
    :param event:
    :param context:
    :return:
    """

    # Get the samplesheet dictionary
    if "samplesheet" not in event.keys():
        logger.error("Could not get samplesheet")
        raise KeyError
    samplesheet_dict = event["samplesheet"]

    # Get the bclconvert_data from the samplesheet
    if "bclconvert_data" not in samplesheet_dict.keys():
        logger.error("Could not get bclconvert_data from samplesheet")
        raise KeyError
    bclconvert_data = samplesheet_dict["bclconvert_data"]

    # Get the unique list of library ids from the samplesheet
    library_id_list = list(
        set(
            list(
                map(
                    lambda bclconvert_data_row_iter_: bclconvert_data_row_iter_.get("sample_id"),
                    bclconvert_data
                )
            )
        )
    )

    # Get library objects
    library_obj_list = get_library_objs(library_id_list)

    # Get all libraries from the database
    return {
        "library_obj_list": library_obj_list
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
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
#
#     # Output
#     # {
#     #   "library_obj_list": [
#     #     {
#     #       "orcabusId": "lib.01J8ES4MPZ5B201R50K42XXM4M",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4EBXK08WDWB97BSCX1C9",
#     #           "projectId": "PO",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4MPHSX7MRCTTFWJBYTT7",
#     #         "sampleId": "MDX210402",
#     #         "externalSampleId": "ZUHR111121",
#     #         "source": "plasma-serum"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4MNXJSDRR406DAXFZP2N",
#     #         "subjectId": "PM3045106"
#     #       },
#     #       "libraryId": "L2400102",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "borderline",
#     #       "type": "WGS",
#     #       "assay": "ctTSO",
#     #       "coverage": 50.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4XMDW0FV1YMWHSZZQ4TX",
#     #         "sampleId": "PTC_SCMM1pc2",
#     #         "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#     #         "source": "cfDNA"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#     #         "subjectId": "CMM1pc-10646259ilm"
#     #       },
#     #       "libraryId": "L2400159",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4XQG3MPBW94TTVT4STVG",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4XQ071BF3WZN111SNJ2B",
#     #         "sampleId": "PTC_SCMM1pc3",
#     #         "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#     #         "source": "cfDNA"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#     #         "subjectId": "CMM1pc-10646259ilm"
#     #       },
#     #       "libraryId": "L2400160",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4XRG9NB38N03688M2CCB",
#     #         "sampleId": "PTC_SCMM1pc4",
#     #         "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#     #         "source": "cfDNA"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#     #         "subjectId": "CMM1pc-10646259ilm"
#     #       },
#     #       "libraryId": "L2400161",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4XWXFANT7P0T3AFXA85G",
#     #         "sampleId": "PTC_SCMM01pc20",
#     #         "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 20ng",
#     #         "source": "cfDNA"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #         "subjectId": "CMM0.1pc-10624819"
#     #       },
#     #       "libraryId": "L2400162",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4XYTSVQVRSBA9M26NSZY",
#     #         "sampleId": "PTC_SCMM01pc15",
#     #         "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 15ng",
#     #         "source": "cfDNA"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #         "subjectId": "CMM0.1pc-10624819"
#     #       },
#     #       "libraryId": "L2400163",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4Y0V0ZBKAE91TDSY0BBB",
#     #         "sampleId": "PTC_SCMM01pc10",
#     #         "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 10ng",
#     #         "source": "cfDNA"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #         "subjectId": "CMM0.1pc-10624819"
#     #       },
#     #       "libraryId": "L2400164",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4Y37JTPEEJSED9BXH8N2",
#     #         "sampleId": "PTC_SCMM01pc5",
#     #         "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 5ng",
#     #         "source": "cfDNA"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #         "subjectId": "CMM0.1pc-10624819"
#     #       },
#     #       "libraryId": "L2400165",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4Y5D52202JVBXHJ9Q9WF",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4Y4XK1WX4WCPD6XY8KNM",
#     #         "sampleId": "NTC_v2ctTSO240207",
#     #         "externalSampleId": "negative control",
#     #         "source": "water"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#     #         "subjectId": "negative control"
#     #       },
#     #       "libraryId": "L2400166",
#     #       "phenotype": "negative-control",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 0.1
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #           "projectId": "CAVATAK",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4ZDAFRK3K3PY33F8XS0W",
#     #         "sampleId": "PRJ240169",
#     #         "externalSampleId": "AUS-006-DRW_C1D1PRE",
#     #         "source": "blood"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#     #         "subjectId": "AUS-006-DRW"
#     #       },
#     #       "libraryId": "L2400191",
#     #       "phenotype": "normal",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #           "projectId": "CAVATAK",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4ZMETZP255WMFC8TSCYT",
#     #         "sampleId": "PRJ240180",
#     #         "externalSampleId": "AUS-006-DRW_Day0",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#     #         "subjectId": "AUS-006-DRW"
#     #       },
#     #       "libraryId": "L2400195",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #           "projectId": "CAVATAK",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4ZNT47EM37QKMT12JPPJ",
#     #         "sampleId": "PRJ240181",
#     #         "externalSampleId": "AUS-006-DRW_Day33",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#     #         "subjectId": "AUS-006-DRW"
#     #       },
#     #       "libraryId": "L2400196",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #           "projectId": "CAVATAK",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4ZQ76H8P0Q7S618F3BMA",
#     #         "sampleId": "PRJ240182",
#     #         "externalSampleId": "AUS-007-JMA_Day0",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4ZEQ3FVD6DDVEG8MW60Q",
#     #         "subjectId": "AUS-007-JMA"
#     #       },
#     #       "libraryId": "L2400197",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #           "projectId": "CAVATAK",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4ZVAR9NQM55Z2TXCDY9V",
#     #         "sampleId": "PRJ240183",
#     #         "externalSampleId": "AUS-007-JMA_Day15",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4ZEQ3FVD6DDVEG8MW60Q",
#     #         "subjectId": "AUS-007-JMA"
#     #       },
#     #       "libraryId": "L2400198",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #           "projectId": "CUP",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES51T84KVVVSEPYQFGW0EV",
#     #         "sampleId": "PRJ240199",
#     #         "externalSampleId": "DNA188239",
#     #         "source": "FFPE"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#     #         "subjectId": "SN_PMC-141"
#     #       },
#     #       "libraryId": "L2400231",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "poor",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 100.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #           "projectId": "CUP",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES527QKB5Y5RVZWZ8HQX0H",
#     #         "sampleId": "PRJ240643",
#     #         "externalSampleId": "DNA188378",
#     #         "source": "blood"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#     #         "subjectId": "SN_PMC-141"
#     #       },
#     #       "libraryId": "L2400238",
#     #       "phenotype": "normal",
#     #       "workflow": "clinical",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #           "projectId": "CUP",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES52A5QX0GQ6RB78Z8DGYQ",
#     #         "sampleId": "PRJ240646",
#     #         "externalSampleId": "DNA189922",
#     #         "source": "blood"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#     #         "subjectId": "SN_PMC-145"
#     #       },
#     #       "libraryId": "L2400239",
#     #       "phenotype": "normal",
#     #       "workflow": "clinical",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #           "projectId": "CUP",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES52BM8BVS3PX47E6FM7D5",
#     #         "sampleId": "PRJ240647",
#     #         "externalSampleId": "DNA189848",
#     #         "source": "FFPE"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#     #         "subjectId": "SN_PMC-145"
#     #       },
#     #       "libraryId": "L2400240",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "poor",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 100.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #           "projectId": "Control",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES52D076FQM5K8128AQ593",
#     #         "sampleId": "NTC_TSqN240226",
#     #         "externalSampleId": "NTC_TSqN240226",
#     #         "source": "water"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#     #         "subjectId": "negative control"
#     #       },
#     #       "libraryId": "L2400241",
#     #       "phenotype": "negative-control",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 0.1
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #           "projectId": "Control",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES52EEX67YRYAJS3F5GMJ5",
#     #         "sampleId": "PTC_TSqN240226",
#     #         "externalSampleId": "NA24385-3",
#     #         "source": "cell-line"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4DRJ31Z2H1GJQZGVDXZR",
#     #         "subjectId": "NA24385"
#     #       },
#     #       "libraryId": "L2400242",
#     #       "phenotype": "normal",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 15.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES52XYMVGRB1Q458THNG4T",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #           "projectId": "Control",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES52XE661E8V8XTWD02QCK",
#     #         "sampleId": "PTC_NebRNA240226",
#     #         "externalSampleId": "Colo829",
#     #         "source": "cell-line"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4GNVGZSJVTHGVKS9VW7F",
#     #         "subjectId": "Colo829"
#     #       },
#     #       "libraryId": "L2400249",
#     #       "phenotype": "tumor",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 1.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #           "projectId": "BPOP-retro",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES4FP9WTFBDNGKVG3D9BD4",
#     #         "sampleId": "PRJ240003",
#     #         "externalSampleId": "3-23BCRL057T",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4FNJ2FCAK0RJST0428X0",
#     #         "subjectId": "23BCRL057T"
#     #       },
#     #       "libraryId": "L2400250",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES530H895X4WA3NQ6CY2QV",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #           "projectId": "BPOP-retro",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES530355YNZ3VHQQQ204PF",
#     #         "sampleId": "PRJ240561",
#     #         "externalSampleId": "4-218-004_Bx",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES51WC4GV5YDJNTMAK2YY1",
#     #         "subjectId": "218-004"
#     #       },
#     #       "libraryId": "L2400251",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #           "projectId": "BPOP-retro",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES531H420JM9MG5R4AE1AZ",
#     #         "sampleId": "PRJ240562",
#     #         "externalSampleId": "5-218-004_04",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES51WC4GV5YDJNTMAK2YY1",
#     #         "subjectId": "218-004"
#     #       },
#     #       "libraryId": "L2400252",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #           "projectId": "BPOP-retro",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES532ZBHWY3DWY0DWQ223R",
#     #         "sampleId": "PRJ240566",
#     #         "externalSampleId": "9-218-007_Bx",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES522WN7YPZS1Z9NGSPNDA",
#     #         "subjectId": "218-007"
#     #       },
#     #       "libraryId": "L2400253",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES534XGBFYDVYV8ZG6SYS0",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #           "projectId": "BPOP-retro",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES534BX7B89X5EKSCFRDDZ",
#     #         "sampleId": "PRJ240567",
#     #         "externalSampleId": "10-218-007_04",
#     #         "source": "tissue"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES522WN7YPZS1Z9NGSPNDA",
#     #         "subjectId": "218-007"
#     #       },
#     #       "libraryId": "L2400254",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "borderline",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #           "projectId": "CUP",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES535VGG93023KWAFMWGH4",
#     #         "sampleId": "PRJ240200",
#     #         "externalSampleId": "RNA036747",
#     #         "source": "FFPE"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#     #         "subjectId": "SN_PMC-141"
#     #       },
#     #       "libraryId": "L2400255",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "very-poor",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES537S0W1AX9PQPST13GM9",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #           "projectId": "CUP",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES5379C40K08YG3JDMZJN7",
#     #         "sampleId": "PRJ240648",
#     #         "externalSampleId": "RNA037080",
#     #         "source": "FFPE"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#     #         "subjectId": "SN_PMC-145"
#     #       },
#     #       "libraryId": "L2400256",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "very-poor",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J8ES5395KETT9T2NJSVNDKNP",
#     #       "projectSet": [
#     #         {
#     #           "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #           "projectId": "Control",
#     #           "name": null,
#     #           "description": null
#     #         }
#     #       ],
#     #       "sample": {
#     #         "orcabusId": "smp.01J8ES538PFF6MQQ35PTC00JAY",
#     #         "sampleId": "NTC_NebRNA240226",
#     #         "externalSampleId": "NTC_NebRNA240226",
#     #         "source": "water"
#     #       },
#     #       "subject": {
#     #         "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#     #         "subjectId": "negative control"
#     #       },
#     #       "libraryId": "L2400257",
#     #       "phenotype": "negative-control",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 0.1
#     #     }
#     #   ]
#     # }
