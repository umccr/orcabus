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
            lambda library_obj_iter: library_obj_iter['internal_id'] in library_id_list,
            get_all_libraries()
        ),
        key=lambda element_iter: element_iter.get("id")
    )


def get_specimen_objs(specimen_id_list: List[int]) -> List[Dict]:
    """
    Get all specimen objects by doing a bulk download + filter rather than query 1-1
    :param specimen_id_list:
    :return:
    """
    specimen_df = pd.DataFrame(
        filter(
            lambda specimen_obj_iter: specimen_obj_iter['id'] in specimen_id_list,
            get_all_specimens()
        )
    )

    # Explode the subjects column
    if 'subjects' in specimen_df.columns:
        specimen_df = specimen_df.explode("subjects")
        specimen_df.rename(
            columns={
                "subjects": "subject"
            },
            inplace=True
        )

    return (
        specimen_df.drop_duplicates().
        sort_values(by='id').
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
            "id": "specimen"
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
        left_on="id",
        right_on="subject",
        how='inner'
    )

    subject_id_list = filtered_subjects_df["id"].tolist()

    return (
        pd.DataFrame(
            filter(
                lambda subject_iter: subject_iter['id'] in subject_id_list,
                all_subjects_list_dict
            )
        ).drop_duplicates().
        sort_values(by='id').
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
#     #       "id": 10723,
#     #       "internal_id": "L2400102",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "borderline",
#     #       "type": "WGS",
#     #       "assay": "ctTSO",
#     #       "coverage": 50.0,
#     #       "specimen": 4077
#     #     },
#     #     {
#     #       "id": 10830,
#     #       "internal_id": "L2400159",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "specimen": 9195
#     #     },
#     #     {
#     #       "id": 10831,
#     #       "internal_id": "L2400160",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "specimen": 9196
#     #     },
#     #     {
#     #       "id": 10832,
#     #       "internal_id": "L2400161",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "specimen": 9197
#     #     },
#     #     {
#     #       "id": 10833,
#     #       "internal_id": "L2400162",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "specimen": 9198
#     #     },
#     #     {
#     #       "id": 10834,
#     #       "internal_id": "L2400163",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "specimen": 9199
#     #     },
#     #     {
#     #       "id": 10835,
#     #       "internal_id": "L2400164",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "specimen": 9200
#     #     },
#     #     {
#     #       "id": 10836,
#     #       "internal_id": "L2400165",
#     #       "phenotype": "tumor",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 38.6,
#     #       "specimen": 9201
#     #     },
#     #     {
#     #       "id": 10837,
#     #       "internal_id": "L2400166",
#     #       "phenotype": "negative-control",
#     #       "workflow": "manual",
#     #       "quality": "good",
#     #       "type": "ctDNA",
#     #       "assay": "ctTSOv2",
#     #       "coverage": 0.1,
#     #       "specimen": 9202
#     #     },
#     #     {
#     #       "id": 10862,
#     #       "internal_id": "L2400191",
#     #       "phenotype": "normal",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0,
#     #       "specimen": 9216
#     #     },
#     #     {
#     #       "id": 10866,
#     #       "internal_id": "L2400195",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "specimen": 9220
#     #     },
#     #     {
#     #       "id": 10867,
#     #       "internal_id": "L2400196",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "specimen": 9221
#     #     },
#     #     {
#     #       "id": 10868,
#     #       "internal_id": "L2400197",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "specimen": 9222
#     #     },
#     #     {
#     #       "id": 10869,
#     #       "internal_id": "L2400198",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 80.0,
#     #       "specimen": 9223
#     #     },
#     #     {
#     #       "id": 10902,
#     #       "internal_id": "L2400231",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "poor",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 100.0,
#     #       "specimen": 9242
#     #     },
#     #     {
#     #       "id": 10909,
#     #       "internal_id": "L2400238",
#     #       "phenotype": "normal",
#     #       "workflow": "clinical",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0,
#     #       "specimen": 9249
#     #     },
#     #     {
#     #       "id": 10910,
#     #       "internal_id": "L2400239",
#     #       "phenotype": "normal",
#     #       "workflow": "clinical",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 40.0,
#     #       "specimen": 9250
#     #     },
#     #     {
#     #       "id": 10911,
#     #       "internal_id": "L2400240",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "poor",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 100.0,
#     #       "specimen": 9251
#     #     },
#     #     {
#     #       "id": 10912,
#     #       "internal_id": "L2400241",
#     #       "phenotype": "negative-control",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 0.1,
#     #       "specimen": 9252
#     #     },
#     #     {
#     #       "id": 10913,
#     #       "internal_id": "L2400242",
#     #       "phenotype": "normal",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WGS",
#     #       "assay": "TsqNano",
#     #       "coverage": 15.0,
#     #       "specimen": 9253
#     #     },
#     #     {
#     #       "id": 10920,
#     #       "internal_id": "L2400249",
#     #       "phenotype": "tumor",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 1.0,
#     #       "specimen": 9260
#     #     },
#     #     {
#     #       "id": 10921,
#     #       "internal_id": "L2400250",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "specimen": 9079
#     #     },
#     #     {
#     #       "id": 10922,
#     #       "internal_id": "L2400251",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "specimen": 9261
#     #     },
#     #     {
#     #       "id": 10923,
#     #       "internal_id": "L2400252",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "specimen": 9262
#     #     },
#     #     {
#     #       "id": 10924,
#     #       "internal_id": "L2400253",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "specimen": 9263
#     #     },
#     #     {
#     #       "id": 10925,
#     #       "internal_id": "L2400254",
#     #       "phenotype": "tumor",
#     #       "workflow": "research",
#     #       "quality": "borderline",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "specimen": 9264
#     #     },
#     #     {
#     #       "id": 10926,
#     #       "internal_id": "L2400255",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "very-poor",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "specimen": 9265
#     #     },
#     #     {
#     #       "id": 10927,
#     #       "internal_id": "L2400256",
#     #       "phenotype": "tumor",
#     #       "workflow": "clinical",
#     #       "quality": "very-poor",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 6.0,
#     #       "specimen": 9266
#     #     },
#     #     {
#     #       "id": 10928,
#     #       "internal_id": "L2400257",
#     #       "phenotype": "negative-control",
#     #       "workflow": "control",
#     #       "quality": "good",
#     #       "type": "WTS",
#     #       "assay": "NebRNA",
#     #       "coverage": 0.1,
#     #       "specimen": 9267
#     #     }
#     #   ],
#     #   "specimen_obj_list": [
#     #     {
#     #       "id": 4077,
#     #       "internal_id": "MDX210402",
#     #       "source": "plasma-serum",
#     #       "subject": 1272
#     #     },
#     #     {
#     #       "id": 9079,
#     #       "internal_id": "PRJ240003",
#     #       "source": "tissue",
#     #       "subject": 3984
#     #     },
#     #     {
#     #       "id": 9195,
#     #       "internal_id": "PTC_SCMM1pc2",
#     #       "source": "cfDNA",
#     #       "subject": 3903
#     #     },
#     #     {
#     #       "id": 9196,
#     #       "internal_id": "PTC_SCMM1pc3",
#     #       "source": "cfDNA",
#     #       "subject": 3903
#     #     },
#     #     {
#     #       "id": 9197,
#     #       "internal_id": "PTC_SCMM1pc4",
#     #       "source": "cfDNA",
#     #       "subject": 3903
#     #     },
#     #     {
#     #       "id": 9198,
#     #       "internal_id": "PTC_SCMM01pc20",
#     #       "source": "cfDNA",
#     #       "subject": 4143
#     #     },
#     #     {
#     #       "id": 9199,
#     #       "internal_id": "PTC_SCMM01pc15",
#     #       "source": "cfDNA",
#     #       "subject": 4143
#     #     },
#     #     {
#     #       "id": 9200,
#     #       "internal_id": "PTC_SCMM01pc10",
#     #       "source": "cfDNA",
#     #       "subject": 4143
#     #     },
#     #     {
#     #       "id": 9201,
#     #       "internal_id": "PTC_SCMM01pc5",
#     #       "source": "cfDNA",
#     #       "subject": 4143
#     #     },
#     #     {
#     #       "id": 9202,
#     #       "internal_id": "NTC_v2ctTSO240207",
#     #       "source": "water",
#     #       "subject": 58
#     #     },
#     #     {
#     #       "id": 9216,
#     #       "internal_id": "PRJ240169",
#     #       "source": "blood",
#     #       "subject": 4148
#     #     },
#     #     {
#     #       "id": 9220,
#     #       "internal_id": "PRJ240180",
#     #       "source": "tissue",
#     #       "subject": 4148
#     #     },
#     #     {
#     #       "id": 9221,
#     #       "internal_id": "PRJ240181",
#     #       "source": "tissue",
#     #       "subject": 4148
#     #     },
#     #     {
#     #       "id": 9222,
#     #       "internal_id": "PRJ240182",
#     #       "source": "tissue",
#     #       "subject": 4149
#     #     },
#     #     {
#     #       "id": 9223,
#     #       "internal_id": "PRJ240183",
#     #       "source": "tissue",
#     #       "subject": 4149
#     #     },
#     #     {
#     #       "id": 9242,
#     #       "internal_id": "PRJ240199",
#     #       "source": "FFPE",
#     #       "subject": 4152
#     #     },
#     #     {
#     #       "id": 9249,
#     #       "internal_id": "PRJ240643",
#     #       "source": "blood",
#     #       "subject": 4152
#     #     },
#     #     {
#     #       "id": 9250,
#     #       "internal_id": "PRJ240646",
#     #       "source": "blood",
#     #       "subject": 4155
#     #     },
#     #     {
#     #       "id": 9251,
#     #       "internal_id": "PRJ240647",
#     #       "source": "FFPE",
#     #       "subject": 4155
#     #     },
#     #     {
#     #       "id": 9252,
#     #       "internal_id": "NTC_TSqN240226",
#     #       "source": "water",
#     #       "subject": 58
#     #     },
#     #     {
#     #       "id": 9253,
#     #       "internal_id": "PTC_TSqN240226",
#     #       "source": "cell-line",
#     #       "subject": 104
#     #     },
#     #     {
#     #       "id": 9260,
#     #       "internal_id": "PTC_NebRNA240226",
#     #       "source": "cell-line",
#     #       "subject": 57
#     #     },
#     #     {
#     #       "id": 9261,
#     #       "internal_id": "PRJ240561",
#     #       "source": "tissue",
#     #       "subject": 4153
#     #     },
#     #     {
#     #       "id": 9262,
#     #       "internal_id": "PRJ240562",
#     #       "source": "tissue",
#     #       "subject": 4153
#     #     },
#     #     {
#     #       "id": 9263,
#     #       "internal_id": "PRJ240566",
#     #       "source": "tissue",
#     #       "subject": 4154
#     #     },
#     #     {
#     #       "id": 9264,
#     #       "internal_id": "PRJ240567",
#     #       "source": "tissue",
#     #       "subject": 4154
#     #     },
#     #     {
#     #       "id": 9265,
#     #       "internal_id": "PRJ240200",
#     #       "source": "FFPE",
#     #       "subject": 4152
#     #     },
#     #     {
#     #       "id": 9266,
#     #       "internal_id": "PRJ240648",
#     #       "source": "FFPE",
#     #       "subject": 4155
#     #     },
#     #     {
#     #       "id": 9267,
#     #       "internal_id": "NTC_NebRNA240226",
#     #       "source": "water",
#     #       "subject": 58
#     #     }
#     #   ],
#     #   "subject_obj_list": [
#     #     {
#     #       "id": 57,
#     #       "internal_id": "SBJ00029"
#     #     },
#     #     {
#     #       "id": 58,
#     #       "internal_id": "SBJ00006"
#     #     },
#     #     {
#     #       "id": 104,
#     #       "internal_id": "SBJ00005"
#     #     },
#     #     {
#     #       "id": 1272,
#     #       "internal_id": "SBJ01143"
#     #     },
#     #     {
#     #       "id": 3903,
#     #       "internal_id": "SBJ04407"
#     #     },
#     #     {
#     #       "id": 3984,
#     #       "internal_id": "SBJ04488"
#     #     },
#     #     {
#     #       "id": 4143,
#     #       "internal_id": "SBJ04648"
#     #     },
#     #     {
#     #       "id": 4148,
#     #       "internal_id": "SBJ04653"
#     #     },
#     #     {
#     #       "id": 4149,
#     #       "internal_id": "SBJ04654"
#     #     },
#     #     {
#     #       "id": 4152,
#     #       "internal_id": "SBJ04659"
#     #     },
#     #     {
#     #       "id": 4153,
#     #       "internal_id": "SBJ04660"
#     #     },
#     #     {
#     #       "id": 4154,
#     #       "internal_id": "SBJ04661"
#     #     },
#     #     {
#     #       "id": 4155,
#     #       "internal_id": "SBJ04662"
#     #     }
#     #   ]
#     # }
