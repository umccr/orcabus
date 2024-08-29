#!/usr/bin/env python3

"""
Get Library Objects from samplesheet
"""

# Standard imports
import logging
from typing import List, Dict

import pandas as pd

# Layer imports
from metadata_tools import get_all_libraries, get_all_specimens, get_all_subjects

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


def get_specimen_objs(specimen_id_list: List[int]) -> List[Dict]:
    """
    Get all specimen objects by doing a bulk download + filter rather than query 1-1
    :param specimen_id_list:
    :return:
    """
    specimen_df = pd.DataFrame(
        filter(
            lambda specimen_obj_iter: specimen_obj_iter['orcabusId'] in specimen_id_list,
            get_all_specimens()
        )
    )

    return (
        specimen_df.drop_duplicates().
        sort_values(by='orcabusId').
        to_dict(orient='records')
    )


def get_specimen_objs_by_library_obj_list(library_obj_list: List[Dict]) -> List[Dict]:
    """
    Get specimen objects by library object list
    :param library_obj_list:
    :return:
    """
    specimen_id_list = list(
        map(
            lambda library_obj_iter: library_obj_iter['specimen'],
            library_obj_list
        )
    )

    # Get the specimens as a dataframe
    specimens_df = pd.DataFrame(get_specimen_objs(specimen_id_list))

    return specimens_df.to_dict(orient='records')


def get_subject_objs_by_specimen_obj_list(specimen_obj_list: List[Dict]) -> List[Dict]:
    """
    Get all subjects by a specimen object list
    :param specimen_obj_list:
    :return:
    """
    # Convert to dataframe to we can coerce columns subjects -> subject
    specimens_df = pd.DataFrame(specimen_obj_list)

    # Since we're merging onto the subject df, we want to rename id to
    # specimen (since the specimen id column is also called specimen in the library dataframe
    # We will also only keep specimen, and subject columns since these are the key linker between the
    # subject and library databases
    specimens_df.rename(
        columns={
            "orcabusId": "specimen"
        },
        inplace=True
    )
    specimens_df = specimens_df[["specimen", "subject"]]

    # Get all subjects
    all_subjects_list_dict = get_all_subjects()
    all_subjects_df = pd.DataFrame(all_subjects_list_dict)

    # Merge specimens and subjects df
    filtered_subjects_df = pd.merge(
        all_subjects_df,
        specimens_df,
        left_on="orcabusId",
        right_on="subject",
        how='inner'
    )

    subject_id_list = filtered_subjects_df["subjectId"].tolist()

    return (
        pd.DataFrame(
            filter(
                lambda subject_iter: subject_iter['subjectId'] in subject_id_list,
                all_subjects_list_dict
            )
        ).drop_duplicates().
        sort_values(by='orcabusId').
        to_dict(orient='records')
    )


def handler(event, context):
    """
    Given a samplesheet dictionary, collect the sample_id attributes as library ids.

    For each unique library id, return the library object
    :param event:
    :param context:
    :return:
    """

    if "samplesheet" not in event.keys():
        logger.error("Could not get samplesheet")
        raise KeyError
    samplesheet_dict = event["samplesheet"]

    if "bclconvert_data" not in samplesheet_dict.keys():
        logger.error("Could not get bclconvert_data from samplesheet")
        raise KeyError
    bclconvert_data = samplesheet_dict["bclconvert_data"]

    # Get the unique list of library ids from the samplesheet
    library_id_list = list(
        set(
            list(
                map(
                    lambda bclconvert_data_row_iter: bclconvert_data_row_iter.get("sample_id"),
                    bclconvert_data
                )
            )
        )
    )

    # Get library objects
    library_obj_list = get_library_objs(library_id_list)

    # Get specimen objects
    specimen_obj_list = get_specimen_objs_by_library_obj_list(library_obj_list)

    # Get subject objects
    subject_obj_list = get_subject_objs_by_specimen_obj_list(specimen_obj_list)

    # Get all libraries from the database
    return {
        "library_obj_list": library_obj_list,
        "specimen_obj_list": specimen_obj_list,
        "subject_obj_list": subject_obj_list
    }


# if __name__ == "__main__":
#     import json
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
#     #       "orcabusId": "lib.01J5S9C4VMJ6PZ8GJ2G189AMXX",
#     #       "libraryId": "L2400102",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "borderline",
#     #       "type": "WGS",
#     #       "assay": "ctTSO",
#     #       "coverage": 50.0,
#     #       "projectOwner": "VCCC",
#     #       "projectName": "PO",
#     #       "specimen": "spc.01J5S9C4V269YTNA17TTP6NF76"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBG0NF8QBNVKM6ESCD60",
#     #       "libraryId": "L2400159",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBFDVZX7ZT3Y6TH28SY4"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBHP6NSB42RVFAP9PGJP",
#     #       "libraryId": "L2400160",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBH4V5B56CEJ5Q1XQKQ9"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBKCATYSFY40BRX6WJWX",
#     #       "libraryId": "L2400161",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBJTBJB72KJ74VSCHKJF"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBN6EAXW4AXG7TQ1H6NC",
#     #       "libraryId": "L2400162",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBMKTX5KN1XMPN479R2M"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBQFX8V1QRW7KAV3MD1W",
#     #       "libraryId": "L2400163",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBPSPN6S3TQCVJZF0XFE"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBS64DNTHK6CE850CCNZ",
#     #       "libraryId": "L2400164",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBRM3Y6PPF6E5NWZA7HG"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBTZRYQNTGAHPC2T601D",
#     #       "libraryId": "L2400165",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBTACFBNJKE8C523B0A7"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CBX10204CK7EKGTH9TMB",
#     #       "libraryId": "L2400166",
#     #       "phenotype": "negative-control",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 0.1,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Testing",
#     #       "specimen": "spc.01J5S9CBWCGKQMG5S3ZSWA2ATE"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CDF8HHG5PJE3ECJMKMY7",
#     #       "libraryId": "L2400191",
#     #       "phenotype": "normal",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0,
#     #       "projectOwner": "TJohn",
#     #       "projectName": "CAVATAK",
#     #       "specimen": "spc.01J5S9CDEH0ATXYAK52KW807R4"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S",
#     #       "libraryId": "L2400195",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "projectOwner": "TJohn",
#     #       "projectName": "CAVATAK",
#     #       "specimen": "spc.01J5S9CDQ0V9T98EGRPQJAP11S"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8",
#     #       "libraryId": "L2400196",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "projectOwner": "TJohn",
#     #       "projectName": "CAVATAK",
#     #       "specimen": "spc.01J5S9CDRZMMR9S784BYSMVWCT"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ",
#     #       "libraryId": "L2400197",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "projectOwner": "TJohn",
#     #       "projectName": "CAVATAK",
#     #       "specimen": "spc.01J5S9CDTSHGYMMJHE3SXEB2JG"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CDXCR7Q5K6A8VJRSMM4Q",
#     #       "libraryId": "L2400198",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "projectOwner": "TJohn",
#     #       "projectName": "CAVATAK",
#     #       "specimen": "spc.01J5S9CDWHAYG4RRG75GYZEK25"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CFX5P69S4KZRQGDFKV1N",
#     #       "libraryId": "L2400231",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "poor",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 100.0,
#     #       "projectOwner": "Tothill",
#     #       "projectName": "CUP",
#     #       "specimen": "spc.01J5S9CFWAQTGK4MZB3HM5NVBC"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CGCAKQWHD9RBM9VXENY9",
#     #       "libraryId": "L2400238",
#     #       "phenotype": "normal",
#     #       "workflow": "clinical",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0,
#     #       "projectOwner": "Tothill",
#     #       "projectName": "CUP",
#     #       "specimen": "spc.01J5S9CGBQCSQCS7XR3T89A82F"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CGEM1DHRQP72EP09B2TA",
#     #       "libraryId": "L2400239",
#     #       "phenotype": "normal",
#     #       "workflow": "clinical",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0,
#     #       "projectOwner": "Tothill",
#     #       "projectName": "CUP",
#     #       "specimen": "spc.01J5S9CGE05BJCJ20M2KP4QWWB"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CGG9N9GH5879SY6A6BJB",
#     #       "libraryId": "L2400240",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "poor",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 100.0,
#     #       "projectOwner": "Tothill",
#     #       "projectName": "CUP",
#     #       "specimen": "spc.01J5S9CGFQM3BQKADX8TWQ4ZH5"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CGJ6G09YQ9KFHPSXMMVD",
#     #       "libraryId": "L2400241",
#     #       "phenotype": "negative-control",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 0.1,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Control",
#     #       "specimen": "spc.01J5S9CGHK1G7YXD7C4FCXXS52"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CGKWDN7STKZKQM3KH9XR",
#     #       "libraryId": "L2400242",
#     #       "phenotype": "normal",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 15.0,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Control",
#     #       "specimen": "spc.01J5S9CGKAT4GHZ1VJFHVV15AD"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CH2SQ0P1SF7WAT5H4DSE",
#     #       "libraryId": "L2400249",
#     #       "phenotype": "tumor",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 1.0,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Control",
#     #       "specimen": "spc.01J5S9CH267XEJP5GMZK31MJWS"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CH4CYPA4SP05H8KRX4W9",
#     #       "libraryId": "L2400250",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "projectOwner": "Whittle",
#     #       "projectName": "BPOP-retro",
#     #       "specimen": "spc.01J5S9C0QC2TBZD7XA26D7WGTW"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CH65E4EE5QJEJ1C60GGG",
#     #       "libraryId": "L2400251",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "projectOwner": "Whittle",
#     #       "projectName": "BPOP-retro",
#     #       "specimen": "spc.01J5S9CH5KXY3VMB9M9J2RCR7B"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CH7TGZMV39Z59WJ8H5GP",
#     #       "libraryId": "L2400252",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "projectOwner": "Whittle",
#     #       "projectName": "BPOP-retro",
#     #       "specimen": "spc.01J5S9CH774HEZFEVWWP2XADK1"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CH9TGMT2TJGBZX5VXHJY",
#     #       "libraryId": "L2400253",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "projectOwner": "Whittle",
#     #       "projectName": "BPOP-retro",
#     #       "specimen": "spc.01J5S9CH98MQ2B1G2BQFEY0XZH"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CHBGAP2XSN4TG8SAMRYY",
#     #       "libraryId": "L2400254",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "borderline",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "projectOwner": "Whittle",
#     #       "projectName": "BPOP-retro",
#     #       "specimen": "spc.01J5S9CHAX3XKJE5XE4VQWYN5H"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CHE4ERQ4H209DH397W8A",
#     #       "libraryId": "L2400255",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "very-poor",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "projectOwner": "Tothill",
#     #       "projectName": "CUP",
#     #       "specimen": "spc.01J5S9CHDGRNK70B043K887RP2"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CHFXPDGYQ8TXHRWQR3PY",
#     #       "libraryId": "L2400256",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "very-poor",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "projectOwner": "Tothill",
#     #       "projectName": "CUP",
#     #       "specimen": "spc.01J5S9CHFAPXYKK49FAGVF5CQF"
#     #     },
#     #     {
#     #       "orcabusId": "lib.01J5S9CHHNGFJN73NPRQMSYGN9",
#     #       "libraryId": "L2400257",
#     #       "phenotype": "negative-control",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 0.1,
#     #       "projectOwner": "UMCCR",
#     #       "projectName": "Control",
#     #       "specimen": "spc.01J5S9CHH24VFM443RD8Q8X4B3"
#     #     }
#     #   ],
#     #   "specimen_obj_list": [
#     #     {
#     #       "orcabusId": "spc.01J5S9C0QC2TBZD7XA26D7WGTW",
#     #       "specimenId": "PRJ240003",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9C0PVB4QNVGK4Q1WSYEGV"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9C4V269YTNA17TTP6NF76",
#     #       "specimenId": "MDX210402",
#     #       "source": "plasma-serum",
#     #       "subject": "sbj.01J5S9C4TE1GCWA1QGNCWHB1Y9"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBFDVZX7ZT3Y6TH28SY4",
#     #       "specimenId": "PTC_SCMM1pc2",
#     #       "source": "cfDNA",
#     #       "subject": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBH4V5B56CEJ5Q1XQKQ9",
#     #       "specimenId": "PTC_SCMM1pc3",
#     #       "source": "cfDNA",
#     #       "subject": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBJTBJB72KJ74VSCHKJF",
#     #       "specimenId": "PTC_SCMM1pc4",
#     #       "source": "cfDNA",
#     #       "subject": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBMKTX5KN1XMPN479R2M",
#     #       "specimenId": "PTC_SCMM01pc20",
#     #       "source": "cfDNA",
#     #       "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBPSPN6S3TQCVJZF0XFE",
#     #       "specimenId": "PTC_SCMM01pc15",
#     #       "source": "cfDNA",
#     #       "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBRM3Y6PPF6E5NWZA7HG",
#     #       "specimenId": "PTC_SCMM01pc10",
#     #       "source": "cfDNA",
#     #       "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBTACFBNJKE8C523B0A7",
#     #       "specimenId": "PTC_SCMM01pc5",
#     #       "source": "cfDNA",
#     #       "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CBWCGKQMG5S3ZSWA2ATE",
#     #       "specimenId": "NTC_v2ctTSO240207",
#     #       "source": "water",
#     #       "subject": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CDEH0ATXYAK52KW807R4",
#     #       "specimenId": "PRJ240169",
#     #       "source": "blood",
#     #       "subject": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CDQ0V9T98EGRPQJAP11S",
#     #       "specimenId": "PRJ240180",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CDRZMMR9S784BYSMVWCT",
#     #       "specimenId": "PRJ240181",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CDTSHGYMMJHE3SXEB2JG",
#     #       "specimenId": "PRJ240182",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CDG7B0KA8YEDK876VVDP"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CDWHAYG4RRG75GYZEK25",
#     #       "specimenId": "PRJ240183",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CDG7B0KA8YEDK876VVDP"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CFWAQTGK4MZB3HM5NVBC",
#     #       "specimenId": "PRJ240199",
#     #       "source": "FFPE",
#     #       "subject": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CGBQCSQCS7XR3T89A82F",
#     #       "specimenId": "PRJ240643",
#     #       "source": "blood",
#     #       "subject": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CGE05BJCJ20M2KP4QWWB",
#     #       "specimenId": "PRJ240646",
#     #       "source": "blood",
#     #       "subject": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CGFQM3BQKADX8TWQ4ZH5",
#     #       "specimenId": "PRJ240647",
#     #       "source": "FFPE",
#     #       "subject": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CGHK1G7YXD7C4FCXXS52",
#     #       "specimenId": "NTC_TSqN240226",
#     #       "source": "water",
#     #       "subject": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CGKAT4GHZ1VJFHVV15AD",
#     #       "specimenId": "PTC_TSqN240226",
#     #       "source": "cell-line",
#     #       "subject": "sbj.01J5S9BYVWZDS8AW7A94CDQBXK"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CH267XEJP5GMZK31MJWS",
#     #       "specimenId": "PTC_NebRNA240226",
#     #       "source": "cell-line",
#     #       "subject": "sbj.01J5S9C1S3XV8PNB78XYJ1EQM1"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CH5KXY3VMB9M9J2RCR7B",
#     #       "specimenId": "PRJ240561",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CH774HEZFEVWWP2XADK1",
#     #       "specimenId": "PRJ240562",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CH98MQ2B1G2BQFEY0XZH",
#     #       "specimenId": "PRJ240566",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CG5GEWYBK0065C49HT23"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CHAX3XKJE5XE4VQWYN5H",
#     #       "specimenId": "PRJ240567",
#     #       "source": "tissue",
#     #       "subject": "sbj.01J5S9CG5GEWYBK0065C49HT23"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CHDGRNK70B043K887RP2",
#     #       "specimenId": "PRJ240200",
#     #       "source": "FFPE",
#     #       "subject": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CHFAPXYKK49FAGVF5CQF",
#     #       "specimenId": "PRJ240648",
#     #       "source": "FFPE",
#     #       "subject": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3"
#     #     },
#     #     {
#     #       "orcabusId": "spc.01J5S9CHH24VFM443RD8Q8X4B3",
#     #       "specimenId": "NTC_NebRNA240226",
#     #       "source": "water",
#     #       "subject": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6"
#     #     }
#     #   ],
#     #   "subject_obj_list": [
#     #     {
#     #       "orcabusId": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6",
#     #       "subjectId": "SBJ00006"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9BYVWZDS8AW7A94CDQBXK",
#     #       "subjectId": "SBJ00005"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9C0PVB4QNVGK4Q1WSYEGV",
#     #       "subjectId": "SBJ04488"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9C1S3XV8PNB78XYJ1EQM1",
#     #       "subjectId": "SBJ00029"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9C4TE1GCWA1QGNCWHB1Y9",
#     #       "subjectId": "SBJ01143"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB",
#     #       "subjectId": "SBJ04407"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0",
#     #       "subjectId": "SBJ04648"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS",
#     #       "subjectId": "SBJ04653"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CDG7B0KA8YEDK876VVDP",
#     #       "subjectId": "SBJ04654"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5",
#     #       "subjectId": "SBJ04659"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN",
#     #       "subjectId": "SBJ04660"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CG5GEWYBK0065C49HT23",
#     #       "subjectId": "SBJ04661"
#     #     },
#     #     {
#     #       "orcabusId": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3",
#     #       "subjectId": "SBJ04662"
#     #     }
#     #   ]
#     # }
