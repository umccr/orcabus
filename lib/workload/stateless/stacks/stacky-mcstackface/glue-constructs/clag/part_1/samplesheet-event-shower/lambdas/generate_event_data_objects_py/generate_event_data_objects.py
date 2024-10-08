#!/usr/bin/env python3

"""
Generate event data objects

Given an instrument run id, samplesheet, library_obj_list, sample_obj_list, subject_obj_list,
Generate the events for

* Start of the SampleSheet Shower
* Library Event Data Objects (library id, plus event data)
* End of the SampleSheet Shower
"""

# Imports
from typing import Dict, List
import pandas as pd
from more_itertools import flatten


# Functions
def get_library_bclconvert_rows(library_obj: Dict, bclconvert_data: List[Dict]) -> List[Dict]:
    """
    Get library bclconvert rows
    :param library_obj:
    :param bclconvert_data:
    :return:
    """
    return list(
        filter(
            lambda bclconvert_row: bclconvert_row.get("sample_id") == library_obj.get("libraryId"),
            bclconvert_data
        )
    )


def generate_library_event_data_object_from_library(
        library_obj: Dict,
        instrument_run_id: str,
        bclconvert_rows: List[Dict]
) -> Dict:
    """
    Generate library event data object from library specimen and subject
    :param library_obj:
    :param instrument_run_id:
    :param bclconvert_rows:
    :return:
    """

    library_event_obj = {
        "orcabusId": library_obj.get("orcabusId"),
        "libraryId": library_obj.get("libraryId"),
        "phenotype": library_obj.get("phenotype", None),
        "workflow": library_obj.get("workflow", None),
        "quality": library_obj.get("quality", None),
        "type": library_obj.get("type", None),
        "assay": library_obj.get("assay", None),
        "coverage": library_obj.get("coverage", None),
    }

    # Trim library event object to non-null values
    library_event_obj = dict(
        filter(
            lambda kv: kv[1] is not None,
            library_event_obj.items()
        )
    )

    # Filter re-key bclconvert data rows
    bclconvert_data_rows_event_obj = []
    fastq_list_row_ids = []

    for bclconvert_row_obj in bclconvert_rows:
        bclconvert_row_event_obj = {
            "sampleId": bclconvert_row_obj.get("sample_id"),
            "index": bclconvert_row_obj.get("index"),
            "index2": bclconvert_row_obj.get("index2", None),
            "lane": bclconvert_row_obj.get("lane"),
            "overrideCycles": bclconvert_row_obj.get("override_cycles", None)
        }

        # Trim bclconvert row event object to non-null values
        bclconvert_row_event_obj = dict(
            filter(
                lambda kv: kv[1] is not None,
                bclconvert_row_event_obj.items()
            )
        )

        bclconvert_data_rows_event_obj.append(bclconvert_row_event_obj)

        fastq_list_row_ids.append(
            {
                "fastqListRowRgid": '.'.join(
                    map(
                        str,
                        filter(
                            lambda x: x is not None,
                            [
                                bclconvert_row_obj.get("index"),
                                bclconvert_row_obj.get("index2", None),
                                bclconvert_row_obj.get("lane"),
                                instrument_run_id,
                                bclconvert_row_obj.get("sample_id"),
                            ]
                        )
                    )
                )
            }
        )

    return {
        "event_data": {
            "instrumentRunId": instrument_run_id,
            "library": library_event_obj,
            "sample": library_obj.get("sample", None),
            "subject": library_obj.get("subject", None),
            "projectSet": library_obj.get("projectSet", None),
            "bclconvertDataRows": bclconvert_data_rows_event_obj,
            "fastqListRows": fastq_list_row_ids,
        }
    }


def handler(event, context):
    """
    Generate the event objects

    :param event:
    :param context:
    :return:
    """

    # Get the instrument run id
    instrument_run_id = event['instrument_run_id']

    # Get the samplesheet
    samplesheet = event['samplesheet']

    # Get the library object list
    library_obj_list = event['library_obj_list']
    library_set = list(set(list(
        map(
            lambda library_obj_iter_: library_obj_iter_.get("orcabusId"),
            library_obj_list
        )
    )))

    # Get sample set from the library object list
    sample_set = list(set(list(
        filter(
            lambda sample_iter_: sample_iter_ is not None,
            map(
                lambda library_obj_iter_: library_obj_iter_.get("sample", {}).get("orcabusId", None),
                library_obj_list
            )
        )
    )))

    # Get the subject set list
    subject_set = list(set(list(
        map(
            lambda library_obj_iter_: library_obj_iter_.get("subject", {}).get("orcabusId", None),
            library_obj_list
        )
    )))

    library_event_data_list = []

    for library_obj in library_obj_list:
        # Get the bclconvert data rows
        bclconvert_rows = get_library_bclconvert_rows(library_obj, samplesheet['bclconvert_data'])

        # Generate the library event data object
        library_event_data_list.append(
            generate_library_event_data_object_from_library(
                library_obj,
                instrument_run_id,
                bclconvert_rows
            )
        )

    # Generate project data level events
    project_obj_list = list(
        flatten(
            list(
                map(
                    lambda library_iter_: library_iter_.get('projectSet'),
                    library_obj_list
                )
            )
        )
    )

    # Drop duplicates
    project_obj_list = pd.DataFrame(
        project_obj_list
    ).drop_duplicates(
        subset='orcabusId'
    ).to_dict(
        orient='records'
    )

    # Generate project set
    project_set = list(set(list(
        map(
            lambda project_obj_iter_: project_obj_iter_.get("orcabusId"),
            project_obj_list
        )
    )))

    project_event_data_list = []
    for project_obj in project_obj_list:
        # Get the library set for this project
        library_proj_obj_list = list(
            filter(
                lambda library_obj_iter: any(
                    map(
                        lambda library_project_iter_: library_project_iter_['orcabusId'] == project_obj['orcabusId'],
                        library_obj_iter.get("projectSet")
                    )
                ),
                library_obj_list
            )
        )

        project_event_data_list.append(
            {
                "event_data": {
                    "instrumentRunId": instrument_run_id,
                    "project": project_obj,
                    "librarySet": list(
                        map(
                            lambda library_obj_iter: {
                                "orcabusId": library_obj_iter.get("orcabusId"),
                                "libraryId": library_obj_iter.get("libraryId")
                            },
                            library_proj_obj_list
                        )
                    )
                }
            }
        )

    # Generate the start shower data
    start_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    # Generate the complete shower event data
    complete_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    return {
        "start_samplesheet_shower_event_data": start_shower_event_data,
        "complete_samplesheet_shower_event_data": complete_shower_event_data,
        "project_event_data_list": project_event_data_list,
        "library_event_data_list": library_event_data_list,
        "library_set": library_set,
        "subject_set": subject_set,
        "project_set": project_set,
        "sample_set": sample_set,
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "instrument_run_id": "240424_A01052_0193_BH7JMMDRX5",
#                     "samplesheet":
#                         {
#                             "header": {
#                                 "file_format_version": 2,
#                                 "run_name": "Tsqn240214-26-ctTSOv2_29Feb24",
#                                 "instrument_type": "NovaSeq"
#                             },
#                             "reads": {
#                                 "read_1_cycles": 151,
#                                 "read_2_cycles": 151,
#                                 "index_1_cycles": 10,
#                                 "index_2_cycles": 10
#                             },
#                             "bclconvert_settings": {
#                                 "minimum_trimmed_read_length": 35,
#                                 "minimum_adapter_overlap": 3,
#                                 "mask_short_reads": 35,
#                                 "software_version": "4.2.7"
#                             },
#                             "bclconvert_data": [
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400102",
#                                     "index": "GAATTCGT",
#                                     "index2": "TTATGAGT",
#                                     "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
#                                 },
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400159",
#                                     "index": "GAGAATGGTT",
#                                     "index2": "TTGCTGCCGA",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400160",
#                                     "index": "AGAGGCAACC",
#                                     "index2": "CCATCATTAG",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400161",
#                                     "index": "CCATCATTAG",
#                                     "index2": "AGAGGCAACC",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400162",
#                                     "index": "GATAGGCCGA",
#                                     "index2": "GCCATGTGCG",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400163",
#                                     "index": "ATGGTTGACT",
#                                     "index2": "AGGACAGGCC",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400164",
#                                     "index": "TATTGCGCTC",
#                                     "index2": "CCTAACACAG",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 1,
#                                     "sample_id": "L2400166",
#                                     "index": "TTCTACATAC",
#                                     "index2": "TTACAGTTAG",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 2,
#                                     "sample_id": "L2400195",
#                                     "index": "ATGAGGCC",
#                                     "index2": "CAATTAAC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 2,
#                                     "sample_id": "L2400196",
#                                     "index": "ACTAAGAT",
#                                     "index2": "CCGCGGTT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 2,
#                                     "sample_id": "L2400197",
#                                     "index": "GTCGGAGC",
#                                     "index2": "TTATAACC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 2,
#                                     "sample_id": "L2400231",
#                                     "index": "TCGTAGTG",
#                                     "index2": "CCAAGTCT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 2,
#                                     "sample_id": "L2400238",
#                                     "index": "GGAGCGTC",
#                                     "index2": "GCACGGAC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 2,
#                                     "sample_id": "L2400239",
#                                     "index": "ATGGCATG",
#                                     "index2": "GGTACCTT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 2,
#                                     "sample_id": "L2400240",
#                                     "index": "GCAATGCA",
#                                     "index2": "AACGTTCC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 3,
#                                     "sample_id": "L2400195",
#                                     "index": "ATGAGGCC",
#                                     "index2": "CAATTAAC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 3,
#                                     "sample_id": "L2400196",
#                                     "index": "ACTAAGAT",
#                                     "index2": "CCGCGGTT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 3,
#                                     "sample_id": "L2400197",
#                                     "index": "GTCGGAGC",
#                                     "index2": "TTATAACC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 3,
#                                     "sample_id": "L2400231",
#                                     "index": "TCGTAGTG",
#                                     "index2": "CCAAGTCT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 3,
#                                     "sample_id": "L2400238",
#                                     "index": "GGAGCGTC",
#                                     "index2": "GCACGGAC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 3,
#                                     "sample_id": "L2400239",
#                                     "index": "ATGGCATG",
#                                     "index2": "GGTACCTT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 3,
#                                     "sample_id": "L2400240",
#                                     "index": "GCAATGCA",
#                                     "index2": "AACGTTCC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400165",
#                                     "index": "ACGCCTTGTT",
#                                     "index2": "ACGTTCCTTA",
#                                     "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
#                                     "adapter_read_1": "CTGTCTCTTATACACATCT",
#                                     "adapter_read_2": "CTGTCTCTTATACACATCT"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400191",
#                                     "index": "GCACGGAC",
#                                     "index2": "TGCGAGAC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400197",
#                                     "index": "GTCGGAGC",
#                                     "index2": "TTATAACC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400198",
#                                     "index": "CTTGGTAT",
#                                     "index2": "GGACTTGG",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400241",
#                                     "index": "GTTCCAAT",
#                                     "index2": "GCAGAATT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400242",
#                                     "index": "ACCTTGGC",
#                                     "index2": "ATGAGGCC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400249",
#                                     "index": "AGTTTCGA",
#                                     "index2": "CCTACGAT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400250",
#                                     "index": "GAACCTCT",
#                                     "index2": "GTCTGCGC",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400251",
#                                     "index": "GCCCAGTG",
#                                     "index2": "CCGCAATT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400252",
#                                     "index": "TGACAGCT",
#                                     "index2": "CCCGTAGG",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400253",
#                                     "index": "CATCACCC",
#                                     "index2": "ATATAGCA",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400254",
#                                     "index": "CTGGAGTA",
#                                     "index2": "GTTCGGTT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400255",
#                                     "index": "GATCCGGG",
#                                     "index2": "AAGCAGGT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400256",
#                                     "index": "AACACCTG",
#                                     "index2": "CGCATGGG",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 },
#                                 {
#                                     "lane": 4,
#                                     "sample_id": "L2400257",
#                                     "index": "GTGACGTT",
#                                     "index2": "TCCCAGAT",
#                                     "override_cycles": "Y151;I8N2;I8N2;Y151"
#                                 }
#                             ],
#                             "cloud_settings": {
#                                 "generated_version": "0.0.0",
#                                 "cloud_workflow": "ica_workflow_1",
#                                 "bclconvert_pipeline": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7"
#                             },
#                             "cloud_data": [
#                                 {
#                                     "sample_id": "L2400102",
#                                     "library_name": "L2400102_GAATTCGT_TTATGAGT",
#                                     "library_prep_kit_name": "ctTSO"
#                                 },
#                                 {
#                                     "sample_id": "L2400159",
#                                     "library_name": "L2400159_GAGAATGGTT_TTGCTGCCGA",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400160",
#                                     "library_name": "L2400160_AGAGGCAACC_CCATCATTAG",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400161",
#                                     "library_name": "L2400161_CCATCATTAG_AGAGGCAACC",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400162",
#                                     "library_name": "L2400162_GATAGGCCGA_GCCATGTGCG",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400163",
#                                     "library_name": "L2400163_ATGGTTGACT_AGGACAGGCC",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400164",
#                                     "library_name": "L2400164_TATTGCGCTC_CCTAACACAG",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400165",
#                                     "library_name": "L2400165_ACGCCTTGTT_ACGTTCCTTA",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400166",
#                                     "library_name": "L2400166_TTCTACATAC_TTACAGTTAG",
#                                     "library_prep_kit_name": "ctTSOv2"
#                                 },
#                                 {
#                                     "sample_id": "L2400191",
#                                     "library_name": "L2400191_GCACGGAC_TGCGAGAC",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400195",
#                                     "library_name": "L2400195_ATGAGGCC_CAATTAAC",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400196",
#                                     "library_name": "L2400196_ACTAAGAT_CCGCGGTT",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400197",
#                                     "library_name": "L2400197_GTCGGAGC_TTATAACC",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400198",
#                                     "library_name": "L2400198_CTTGGTAT_GGACTTGG",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400231",
#                                     "library_name": "L2400231_TCGTAGTG_CCAAGTCT",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400238",
#                                     "library_name": "L2400238_GGAGCGTC_GCACGGAC",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400239",
#                                     "library_name": "L2400239_ATGGCATG_GGTACCTT",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400240",
#                                     "library_name": "L2400240_GCAATGCA_AACGTTCC",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400241",
#                                     "library_name": "L2400241_GTTCCAAT_GCAGAATT",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400242",
#                                     "library_name": "L2400242_ACCTTGGC_ATGAGGCC",
#                                     "library_prep_kit_name": "TsqNano"
#                                 },
#                                 {
#                                     "sample_id": "L2400249",
#                                     "library_name": "L2400249_AGTTTCGA_CCTACGAT",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400250",
#                                     "library_name": "L2400250_GAACCTCT_GTCTGCGC",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400251",
#                                     "library_name": "L2400251_GCCCAGTG_CCGCAATT",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400252",
#                                     "library_name": "L2400252_TGACAGCT_CCCGTAGG",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400253",
#                                     "library_name": "L2400253_CATCACCC_ATATAGCA",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400254",
#                                     "library_name": "L2400254_CTGGAGTA_GTTCGGTT",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400255",
#                                     "library_name": "L2400255_GATCCGGG_AAGCAGGT",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400256",
#                                     "library_name": "L2400256_AACACCTG_CGCATGGG",
#                                     "library_prep_kit_name": "NebRNA"
#                                 },
#                                 {
#                                     "sample_id": "L2400257",
#                                     "library_name": "L2400257_GTGACGTT_TCCCAGAT",
#                                     "library_prep_kit_name": "NebRNA"
#                                 }
#                             ]
#                         },
#                     "library_obj_list": [
#                         {
#                             "orcabusId": "lib.01J8ES4MPZ5B201R50K42XXM4M",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4EBXK08WDWB97BSCX1C9",
#                                     "projectId": "PO",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4MPHSX7MRCTTFWJBYTT7",
#                                 "sampleId": "MDX210402",
#                                 "externalSampleId": "ZUHR111121",
#                                 "source": "plasma-serum"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4MNXJSDRR406DAXFZP2N",
#                                 "subjectId": "PM3045106"
#                             },
#                             "libraryId": "L2400102",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "borderline",
#                             "type": "WGS",
#                             "assay": "ctTSO",
#                             "coverage": 50.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4XMDW0FV1YMWHSZZQ4TX",
#                                 "sampleId": "PTC_SCMM1pc2",
#                                 "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#                                 "source": "cfDNA"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#                                 "subjectId": "CMM1pc-10646259ilm"
#                             },
#                             "libraryId": "L2400159",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XQG3MPBW94TTVT4STVG",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4XQ071BF3WZN111SNJ2B",
#                                 "sampleId": "PTC_SCMM1pc3",
#                                 "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#                                 "source": "cfDNA"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#                                 "subjectId": "CMM1pc-10646259ilm"
#                             },
#                             "libraryId": "L2400160",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4XRG9NB38N03688M2CCB",
#                                 "sampleId": "PTC_SCMM1pc4",
#                                 "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#                                 "source": "cfDNA"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#                                 "subjectId": "CMM1pc-10646259ilm"
#                             },
#                             "libraryId": "L2400161",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4XWXFANT7P0T3AFXA85G",
#                                 "sampleId": "PTC_SCMM01pc20",
#                                 "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 20ng",
#                                 "source": "cfDNA"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#                                 "subjectId": "CMM0.1pc-10624819"
#                             },
#                             "libraryId": "L2400162",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4XYTSVQVRSBA9M26NSZY",
#                                 "sampleId": "PTC_SCMM01pc15",
#                                 "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 15ng",
#                                 "source": "cfDNA"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#                                 "subjectId": "CMM0.1pc-10624819"
#                             },
#                             "libraryId": "L2400163",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4Y0V0ZBKAE91TDSY0BBB",
#                                 "sampleId": "PTC_SCMM01pc10",
#                                 "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 10ng",
#                                 "source": "cfDNA"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#                                 "subjectId": "CMM0.1pc-10624819"
#                             },
#                             "libraryId": "L2400164",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4Y37JTPEEJSED9BXH8N2",
#                                 "sampleId": "PTC_SCMM01pc5",
#                                 "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 5ng",
#                                 "source": "cfDNA"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#                                 "subjectId": "CMM0.1pc-10624819"
#                             },
#                             "libraryId": "L2400165",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4Y5D52202JVBXHJ9Q9WF",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#                                     "projectId": "Testing",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4Y4XK1WX4WCPD6XY8KNM",
#                                 "sampleId": "NTC_v2ctTSO240207",
#                                 "externalSampleId": "negative control",
#                                 "source": "water"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#                                 "subjectId": "negative control"
#                             },
#                             "libraryId": "L2400166",
#                             "phenotype": "negative-control",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 0.1
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#                                     "projectId": "CAVATAK",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4ZDAFRK3K3PY33F8XS0W",
#                                 "sampleId": "PRJ240169",
#                                 "externalSampleId": "AUS-006-DRW_C1D1PRE",
#                                 "source": "blood"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#                                 "subjectId": "AUS-006-DRW"
#                             },
#                             "libraryId": "L2400191",
#                             "phenotype": "normal",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#                                     "projectId": "CAVATAK",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4ZMETZP255WMFC8TSCYT",
#                                 "sampleId": "PRJ240180",
#                                 "externalSampleId": "AUS-006-DRW_Day0",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#                                 "subjectId": "AUS-006-DRW"
#                             },
#                             "libraryId": "L2400195",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#                                     "projectId": "CAVATAK",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4ZNT47EM37QKMT12JPPJ",
#                                 "sampleId": "PRJ240181",
#                                 "externalSampleId": "AUS-006-DRW_Day33",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#                                 "subjectId": "AUS-006-DRW"
#                             },
#                             "libraryId": "L2400196",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#                                     "projectId": "CAVATAK",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4ZQ76H8P0Q7S618F3BMA",
#                                 "sampleId": "PRJ240182",
#                                 "externalSampleId": "AUS-007-JMA_Day0",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4ZEQ3FVD6DDVEG8MW60Q",
#                                 "subjectId": "AUS-007-JMA"
#                             },
#                             "libraryId": "L2400197",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#                                     "projectId": "CAVATAK",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4ZVAR9NQM55Z2TXCDY9V",
#                                 "sampleId": "PRJ240183",
#                                 "externalSampleId": "AUS-007-JMA_Day15",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4ZEQ3FVD6DDVEG8MW60Q",
#                                 "subjectId": "AUS-007-JMA"
#                             },
#                             "libraryId": "L2400198",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#                                     "projectId": "CUP",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES51T84KVVVSEPYQFGW0EV",
#                                 "sampleId": "PRJ240199",
#                                 "externalSampleId": "DNA188239",
#                                 "source": "FFPE"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#                                 "subjectId": "SN_PMC-141"
#                             },
#                             "libraryId": "L2400231",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "poor",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 100.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#                                     "projectId": "CUP",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES527QKB5Y5RVZWZ8HQX0H",
#                                 "sampleId": "PRJ240643",
#                                 "externalSampleId": "DNA188378",
#                                 "source": "blood"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#                                 "subjectId": "SN_PMC-141"
#                             },
#                             "libraryId": "L2400238",
#                             "phenotype": "normal",
#                             "workflow": "clinical",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#                                     "projectId": "CUP",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES52A5QX0GQ6RB78Z8DGYQ",
#                                 "sampleId": "PRJ240646",
#                                 "externalSampleId": "DNA189922",
#                                 "source": "blood"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#                                 "subjectId": "SN_PMC-145"
#                             },
#                             "libraryId": "L2400239",
#                             "phenotype": "normal",
#                             "workflow": "clinical",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#                                     "projectId": "CUP",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES52BM8BVS3PX47E6FM7D5",
#                                 "sampleId": "PRJ240647",
#                                 "externalSampleId": "DNA189848",
#                                 "source": "FFPE"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#                                 "subjectId": "SN_PMC-145"
#                             },
#                             "libraryId": "L2400240",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "poor",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 100.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#                                     "projectId": "Control",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES52D076FQM5K8128AQ593",
#                                 "sampleId": "NTC_TSqN240226",
#                                 "externalSampleId": "NTC_TSqN240226",
#                                 "source": "water"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#                                 "subjectId": "negative control"
#                             },
#                             "libraryId": "L2400241",
#                             "phenotype": "negative-control",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 0.1
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#                                     "projectId": "Control",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES52EEX67YRYAJS3F5GMJ5",
#                                 "sampleId": "PTC_TSqN240226",
#                                 "externalSampleId": "NA24385-3",
#                                 "source": "cell-line"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4DRJ31Z2H1GJQZGVDXZR",
#                                 "subjectId": "NA24385"
#                             },
#                             "libraryId": "L2400242",
#                             "phenotype": "normal",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 15.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52XYMVGRB1Q458THNG4T",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#                                     "projectId": "Control",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES52XE661E8V8XTWD02QCK",
#                                 "sampleId": "PTC_NebRNA240226",
#                                 "externalSampleId": "Colo829",
#                                 "source": "cell-line"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4GNVGZSJVTHGVKS9VW7F",
#                                 "subjectId": "Colo829"
#                             },
#                             "libraryId": "L2400249",
#                             "phenotype": "tumor",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 1.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#                                     "projectId": "BPOP-retro",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES4FP9WTFBDNGKVG3D9BD4",
#                                 "sampleId": "PRJ240003",
#                                 "externalSampleId": "3-23BCRL057T",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4FNJ2FCAK0RJST0428X0",
#                                 "subjectId": "23BCRL057T"
#                             },
#                             "libraryId": "L2400250",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES530H895X4WA3NQ6CY2QV",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#                                     "projectId": "BPOP-retro",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES530355YNZ3VHQQQ204PF",
#                                 "sampleId": "PRJ240561",
#                                 "externalSampleId": "4-218-004_Bx",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES51WC4GV5YDJNTMAK2YY1",
#                                 "subjectId": "218-004"
#                             },
#                             "libraryId": "L2400251",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#                                     "projectId": "BPOP-retro",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES531H420JM9MG5R4AE1AZ",
#                                 "sampleId": "PRJ240562",
#                                 "externalSampleId": "5-218-004_04",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES51WC4GV5YDJNTMAK2YY1",
#                                 "subjectId": "218-004"
#                             },
#                             "libraryId": "L2400252",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#                                     "projectId": "BPOP-retro",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES532ZBHWY3DWY0DWQ223R",
#                                 "sampleId": "PRJ240566",
#                                 "externalSampleId": "9-218-007_Bx",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES522WN7YPZS1Z9NGSPNDA",
#                                 "subjectId": "218-007"
#                             },
#                             "libraryId": "L2400253",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES534XGBFYDVYV8ZG6SYS0",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#                                     "projectId": "BPOP-retro",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES534BX7B89X5EKSCFRDDZ",
#                                 "sampleId": "PRJ240567",
#                                 "externalSampleId": "10-218-007_04",
#                                 "source": "tissue"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES522WN7YPZS1Z9NGSPNDA",
#                                 "subjectId": "218-007"
#                             },
#                             "libraryId": "L2400254",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "borderline",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#                                     "projectId": "CUP",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES535VGG93023KWAFMWGH4",
#                                 "sampleId": "PRJ240200",
#                                 "externalSampleId": "RNA036747",
#                                 "source": "FFPE"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#                                 "subjectId": "SN_PMC-141"
#                             },
#                             "libraryId": "L2400255",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "very-poor",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES537S0W1AX9PQPST13GM9",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#                                     "projectId": "CUP",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES5379C40K08YG3JDMZJN7",
#                                 "sampleId": "PRJ240648",
#                                 "externalSampleId": "RNA037080",
#                                 "source": "FFPE"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#                                 "subjectId": "SN_PMC-145"
#                             },
#                             "libraryId": "L2400256",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "very-poor",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES5395KETT9T2NJSVNDKNP",
#                             "projectSet": [
#                                 {
#                                     "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#                                     "projectId": "Control",
#                                     "name": None,
#                                     "description": None
#                                 }
#                             ],
#                             "sample": {
#                                 "orcabusId": "smp.01J8ES538PFF6MQQ35PTC00JAY",
#                                 "sampleId": "NTC_NebRNA240226",
#                                 "externalSampleId": "NTC_NebRNA240226",
#                                 "source": "water"
#                             },
#                             "subject": {
#                                 "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#                                 "subjectId": "negative control"
#                             },
#                             "libraryId": "L2400257",
#                             "phenotype": "negative-control",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 0.1
#                         }
#                     ],
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "start_samplesheet_shower_event_data": {
#     #     "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5"
#     #   },
#     #   "complete_samplesheet_shower_event_data": {
#     #     "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5"
#     #   },
#     #   "project_event_data_list": [
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "project": {
#     #           "orcabusId": "prj.01J8ES4EBXK08WDWB97BSCX1C9",
#     #           "projectId": "PO",
#     #           "name": null,
#     #           "description": null
#     #         },
#     #         "librarySet": [
#     #           {
#     #             "orcabusId": "lib.01J8ES4MPZ5B201R50K42XXM4M",
#     #             "libraryId": "L2400102"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "project": {
#     #           "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #           "projectId": "Testing",
#     #           "name": null,
#     #           "description": null
#     #         },
#     #         "librarySet": [
#     #           {
#     #             "orcabusId": "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#     #             "libraryId": "L2400159"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4XQG3MPBW94TTVT4STVG",
#     #             "libraryId": "L2400160"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#     #             "libraryId": "L2400161"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#     #             "libraryId": "L2400162"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#     #             "libraryId": "L2400163"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#     #             "libraryId": "L2400164"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#     #             "libraryId": "L2400165"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4Y5D52202JVBXHJ9Q9WF",
#     #             "libraryId": "L2400166"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "project": {
#     #           "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #           "projectId": "CAVATAK",
#     #           "name": null,
#     #           "description": null
#     #         },
#     #         "librarySet": [
#     #           {
#     #             "orcabusId": "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#     #             "libraryId": "L2400191"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#     #             "libraryId": "L2400195"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#     #             "libraryId": "L2400196"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ",
#     #             "libraryId": "L2400197"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9",
#     #             "libraryId": "L2400198"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "project": {
#     #           "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #           "projectId": "CUP",
#     #           "name": null,
#     #           "description": null
#     #         },
#     #         "librarySet": [
#     #           {
#     #             "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED",
#     #             "libraryId": "L2400231"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0",
#     #             "libraryId": "L2400238"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#     #             "libraryId": "L2400239"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83",
#     #             "libraryId": "L2400240"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#     #             "libraryId": "L2400255"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES537S0W1AX9PQPST13GM9",
#     #             "libraryId": "L2400256"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "project": {
#     #           "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #           "projectId": "Control",
#     #           "name": null,
#     #           "description": null
#     #         },
#     #         "librarySet": [
#     #           {
#     #             "orcabusId": "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#     #             "libraryId": "L2400241"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#     #             "libraryId": "L2400242"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES52XYMVGRB1Q458THNG4T",
#     #             "libraryId": "L2400249"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES5395KETT9T2NJSVNDKNP",
#     #             "libraryId": "L2400257"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "project": {
#     #           "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #           "projectId": "BPOP-retro",
#     #           "name": null,
#     #           "description": null
#     #         },
#     #         "librarySet": [
#     #           {
#     #             "orcabusId": "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#     #             "libraryId": "L2400250"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES530H895X4WA3NQ6CY2QV",
#     #             "libraryId": "L2400251"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#     #             "libraryId": "L2400252"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#     #             "libraryId": "L2400253"
#     #           },
#     #           {
#     #             "orcabusId": "lib.01J8ES534XGBFYDVYV8ZG6SYS0",
#     #             "libraryId": "L2400254"
#     #           }
#     #         ]
#     #       }
#     #     }
#     #   ],
#     #   "library_event_data_list": [
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4MPZ5B201R50K42XXM4M",
#     #           "libraryId": "L2400102",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "borderline",
#     #           "type": "WGS",
#     #           "assay": "ctTSO",
#     #           "coverage": 50.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4MPHSX7MRCTTFWJBYTT7",
#     #           "sampleId": "MDX210402",
#     #           "externalSampleId": "ZUHR111121",
#     #           "source": "plasma-serum"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4MNXJSDRR406DAXFZP2N",
#     #           "subjectId": "PM3045106"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4EBXK08WDWB97BSCX1C9",
#     #             "projectId": "PO",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400102",
#     #             "index": "GAATTCGT",
#     #             "index2": "TTATGAGT",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GAATTCGT.TTATGAGT.1.240424_A01052_0193_BH7JMMDRX5.L2400102"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#     #           "libraryId": "L2400159",
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4XMDW0FV1YMWHSZZQ4TX",
#     #           "sampleId": "PTC_SCMM1pc2",
#     #           "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#     #           "source": "cfDNA"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#     #           "subjectId": "CMM1pc-10646259ilm"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400159",
#     #             "index": "GAGAATGGTT",
#     #             "index2": "TTGCTGCCGA",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GAGAATGGTT.TTGCTGCCGA.1.240424_A01052_0193_BH7JMMDRX5.L2400159"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4XQG3MPBW94TTVT4STVG",
#     #           "libraryId": "L2400160",
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4XQ071BF3WZN111SNJ2B",
#     #           "sampleId": "PTC_SCMM1pc3",
#     #           "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#     #           "source": "cfDNA"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#     #           "subjectId": "CMM1pc-10646259ilm"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400160",
#     #             "index": "AGAGGCAACC",
#     #             "index2": "CCATCATTAG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "AGAGGCAACC.CCATCATTAG.1.240424_A01052_0193_BH7JMMDRX5.L2400160"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#     #           "libraryId": "L2400161",
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4XRG9NB38N03688M2CCB",
#     #           "sampleId": "PTC_SCMM1pc4",
#     #           "externalSampleId": "SSq-CompMM-1pc-10646259ilm",
#     #           "source": "cfDNA"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#     #           "subjectId": "CMM1pc-10646259ilm"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400161",
#     #             "index": "CCATCATTAG",
#     #             "index2": "AGAGGCAACC",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "CCATCATTAG.AGAGGCAACC.1.240424_A01052_0193_BH7JMMDRX5.L2400161"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#     #           "libraryId": "L2400162",
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4XWXFANT7P0T3AFXA85G",
#     #           "sampleId": "PTC_SCMM01pc20",
#     #           "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 20ng",
#     #           "source": "cfDNA"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #           "subjectId": "CMM0.1pc-10624819"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400162",
#     #             "index": "GATAGGCCGA",
#     #             "index2": "GCCATGTGCG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GATAGGCCGA.GCCATGTGCG.1.240424_A01052_0193_BH7JMMDRX5.L2400162"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#     #           "libraryId": "L2400163",
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4XYTSVQVRSBA9M26NSZY",
#     #           "sampleId": "PTC_SCMM01pc15",
#     #           "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 15ng",
#     #           "source": "cfDNA"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #           "subjectId": "CMM0.1pc-10624819"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400163",
#     #             "index": "ATGGTTGACT",
#     #             "index2": "AGGACAGGCC",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "ATGGTTGACT.AGGACAGGCC.1.240424_A01052_0193_BH7JMMDRX5.L2400163"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#     #           "libraryId": "L2400164",
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4Y0V0ZBKAE91TDSY0BBB",
#     #           "sampleId": "PTC_SCMM01pc10",
#     #           "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 10ng",
#     #           "source": "cfDNA"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #           "subjectId": "CMM0.1pc-10624819"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400164",
#     #             "index": "TATTGCGCTC",
#     #             "index2": "CCTAACACAG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "TATTGCGCTC.CCTAACACAG.1.240424_A01052_0193_BH7JMMDRX5.L2400164"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#     #           "libraryId": "L2400165",
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4Y37JTPEEJSED9BXH8N2",
#     #           "sampleId": "PTC_SCMM01pc5",
#     #           "externalSampleId": "SSq-CompMM-0.1pc-10624819 - 5ng",
#     #           "source": "cfDNA"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #           "subjectId": "CMM0.1pc-10624819"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400165",
#     #             "index": "ACGCCTTGTT",
#     #             "index2": "ACGTTCCTTA",
#     #             "lane": 4,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "ACGCCTTGTT.ACGTTCCTTA.4.240424_A01052_0193_BH7JMMDRX5.L2400165"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4Y5D52202JVBXHJ9Q9WF",
#     #           "libraryId": "L2400166",
#     #           "phenotype": "negative-control",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 0.1
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4Y4XK1WX4WCPD6XY8KNM",
#     #           "sampleId": "NTC_v2ctTSO240207",
#     #           "externalSampleId": "negative control",
#     #           "source": "water"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#     #           "subjectId": "negative control"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1",
#     #             "projectId": "Testing",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400166",
#     #             "index": "TTCTACATAC",
#     #             "index2": "TTACAGTTAG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "TTCTACATAC.TTACAGTTAG.1.240424_A01052_0193_BH7JMMDRX5.L2400166"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#     #           "libraryId": "L2400191",
#     #           "phenotype": "normal",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 40.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4ZDAFRK3K3PY33F8XS0W",
#     #           "sampleId": "PRJ240169",
#     #           "externalSampleId": "AUS-006-DRW_C1D1PRE",
#     #           "source": "blood"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#     #           "subjectId": "AUS-006-DRW"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #             "projectId": "CAVATAK",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400191",
#     #             "index": "GCACGGAC",
#     #             "index2": "TGCGAGAC",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GCACGGAC.TGCGAGAC.4.240424_A01052_0193_BH7JMMDRX5.L2400191"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#     #           "libraryId": "L2400195",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4ZMETZP255WMFC8TSCYT",
#     #           "sampleId": "PRJ240180",
#     #           "externalSampleId": "AUS-006-DRW_Day0",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#     #           "subjectId": "AUS-006-DRW"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #             "projectId": "CAVATAK",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400195",
#     #             "index": "ATGAGGCC",
#     #             "index2": "CAATTAAC",
#     #             "lane": 2,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400195",
#     #             "index": "ATGAGGCC",
#     #             "index2": "CAATTAAC",
#     #             "lane": 3,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "ATGAGGCC.CAATTAAC.2.240424_A01052_0193_BH7JMMDRX5.L2400195"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "ATGAGGCC.CAATTAAC.3.240424_A01052_0193_BH7JMMDRX5.L2400195"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#     #           "libraryId": "L2400196",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4ZNT47EM37QKMT12JPPJ",
#     #           "sampleId": "PRJ240181",
#     #           "externalSampleId": "AUS-006-DRW_Day33",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#     #           "subjectId": "AUS-006-DRW"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #             "projectId": "CAVATAK",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400196",
#     #             "index": "ACTAAGAT",
#     #             "index2": "CCGCGGTT",
#     #             "lane": 2,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400196",
#     #             "index": "ACTAAGAT",
#     #             "index2": "CCGCGGTT",
#     #             "lane": 3,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "ACTAAGAT.CCGCGGTT.2.240424_A01052_0193_BH7JMMDRX5.L2400196"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "ACTAAGAT.CCGCGGTT.3.240424_A01052_0193_BH7JMMDRX5.L2400196"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ",
#     #           "libraryId": "L2400197",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4ZQ76H8P0Q7S618F3BMA",
#     #           "sampleId": "PRJ240182",
#     #           "externalSampleId": "AUS-007-JMA_Day0",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4ZEQ3FVD6DDVEG8MW60Q",
#     #           "subjectId": "AUS-007-JMA"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #             "projectId": "CAVATAK",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400197",
#     #             "index": "GTCGGAGC",
#     #             "index2": "TTATAACC",
#     #             "lane": 2,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400197",
#     #             "index": "GTCGGAGC",
#     #             "index2": "TTATAACC",
#     #             "lane": 3,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400197",
#     #             "index": "GTCGGAGC",
#     #             "index2": "TTATAACC",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GTCGGAGC.TTATAACC.2.240424_A01052_0193_BH7JMMDRX5.L2400197"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "GTCGGAGC.TTATAACC.3.240424_A01052_0193_BH7JMMDRX5.L2400197"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "GTCGGAGC.TTATAACC.4.240424_A01052_0193_BH7JMMDRX5.L2400197"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9",
#     #           "libraryId": "L2400198",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4ZVAR9NQM55Z2TXCDY9V",
#     #           "sampleId": "PRJ240183",
#     #           "externalSampleId": "AUS-007-JMA_Day15",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4ZEQ3FVD6DDVEG8MW60Q",
#     #           "subjectId": "AUS-007-JMA"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #             "projectId": "CAVATAK",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400198",
#     #             "index": "CTTGGTAT",
#     #             "index2": "GGACTTGG",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "CTTGGTAT.GGACTTGG.4.240424_A01052_0193_BH7JMMDRX5.L2400198"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED",
#     #           "libraryId": "L2400231",
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "poor",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 100.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES51T84KVVVSEPYQFGW0EV",
#     #           "sampleId": "PRJ240199",
#     #           "externalSampleId": "DNA188239",
#     #           "source": "FFPE"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#     #           "subjectId": "SN_PMC-141"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #             "projectId": "CUP",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400231",
#     #             "index": "TCGTAGTG",
#     #             "index2": "CCAAGTCT",
#     #             "lane": 2,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400231",
#     #             "index": "TCGTAGTG",
#     #             "index2": "CCAAGTCT",
#     #             "lane": 3,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "TCGTAGTG.CCAAGTCT.2.240424_A01052_0193_BH7JMMDRX5.L2400231"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "TCGTAGTG.CCAAGTCT.3.240424_A01052_0193_BH7JMMDRX5.L2400231"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0",
#     #           "libraryId": "L2400238",
#     #           "phenotype": "normal",
#     #           "workflow": "clinical",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 40.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES527QKB5Y5RVZWZ8HQX0H",
#     #           "sampleId": "PRJ240643",
#     #           "externalSampleId": "DNA188378",
#     #           "source": "blood"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#     #           "subjectId": "SN_PMC-141"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #             "projectId": "CUP",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400238",
#     #             "index": "GGAGCGTC",
#     #             "index2": "GCACGGAC",
#     #             "lane": 2,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400238",
#     #             "index": "GGAGCGTC",
#     #             "index2": "GCACGGAC",
#     #             "lane": 3,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GGAGCGTC.GCACGGAC.2.240424_A01052_0193_BH7JMMDRX5.L2400238"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "GGAGCGTC.GCACGGAC.3.240424_A01052_0193_BH7JMMDRX5.L2400238"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#     #           "libraryId": "L2400239",
#     #           "phenotype": "normal",
#     #           "workflow": "clinical",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 40.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES52A5QX0GQ6RB78Z8DGYQ",
#     #           "sampleId": "PRJ240646",
#     #           "externalSampleId": "DNA189922",
#     #           "source": "blood"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#     #           "subjectId": "SN_PMC-145"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #             "projectId": "CUP",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400239",
#     #             "index": "ATGGCATG",
#     #             "index2": "GGTACCTT",
#     #             "lane": 2,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400239",
#     #             "index": "ATGGCATG",
#     #             "index2": "GGTACCTT",
#     #             "lane": 3,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "ATGGCATG.GGTACCTT.2.240424_A01052_0193_BH7JMMDRX5.L2400239"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "ATGGCATG.GGTACCTT.3.240424_A01052_0193_BH7JMMDRX5.L2400239"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83",
#     #           "libraryId": "L2400240",
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "poor",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 100.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES52BM8BVS3PX47E6FM7D5",
#     #           "sampleId": "PRJ240647",
#     #           "externalSampleId": "DNA189848",
#     #           "source": "FFPE"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#     #           "subjectId": "SN_PMC-145"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #             "projectId": "CUP",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400240",
#     #             "index": "GCAATGCA",
#     #             "index2": "AACGTTCC",
#     #             "lane": 2,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           },
#     #           {
#     #             "sampleId": "L2400240",
#     #             "index": "GCAATGCA",
#     #             "index2": "AACGTTCC",
#     #             "lane": 3,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GCAATGCA.AACGTTCC.2.240424_A01052_0193_BH7JMMDRX5.L2400240"
#     #           },
#     #           {
#     #             "fastqListRowRgid": "GCAATGCA.AACGTTCC.3.240424_A01052_0193_BH7JMMDRX5.L2400240"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#     #           "libraryId": "L2400241",
#     #           "phenotype": "negative-control",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 0.1
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES52D076FQM5K8128AQ593",
#     #           "sampleId": "NTC_TSqN240226",
#     #           "externalSampleId": "NTC_TSqN240226",
#     #           "source": "water"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#     #           "subjectId": "negative control"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #             "projectId": "Control",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400241",
#     #             "index": "GTTCCAAT",
#     #             "index2": "GCAGAATT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GTTCCAAT.GCAGAATT.4.240424_A01052_0193_BH7JMMDRX5.L2400241"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#     #           "libraryId": "L2400242",
#     #           "phenotype": "normal",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 15.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES52EEX67YRYAJS3F5GMJ5",
#     #           "sampleId": "PTC_TSqN240226",
#     #           "externalSampleId": "NA24385-3",
#     #           "source": "cell-line"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4DRJ31Z2H1GJQZGVDXZR",
#     #           "subjectId": "NA24385"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #             "projectId": "Control",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400242",
#     #             "index": "ACCTTGGC",
#     #             "index2": "ATGAGGCC",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "ACCTTGGC.ATGAGGCC.4.240424_A01052_0193_BH7JMMDRX5.L2400242"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES52XYMVGRB1Q458THNG4T",
#     #           "libraryId": "L2400249",
#     #           "phenotype": "tumor",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 1.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES52XE661E8V8XTWD02QCK",
#     #           "sampleId": "PTC_NebRNA240226",
#     #           "externalSampleId": "Colo829",
#     #           "source": "cell-line"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4GNVGZSJVTHGVKS9VW7F",
#     #           "subjectId": "Colo829"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #             "projectId": "Control",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400249",
#     #             "index": "AGTTTCGA",
#     #             "index2": "CCTACGAT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "AGTTTCGA.CCTACGAT.4.240424_A01052_0193_BH7JMMDRX5.L2400249"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#     #           "libraryId": "L2400250",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES4FP9WTFBDNGKVG3D9BD4",
#     #           "sampleId": "PRJ240003",
#     #           "externalSampleId": "3-23BCRL057T",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4FNJ2FCAK0RJST0428X0",
#     #           "subjectId": "23BCRL057T"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #             "projectId": "BPOP-retro",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400250",
#     #             "index": "GAACCTCT",
#     #             "index2": "GTCTGCGC",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GAACCTCT.GTCTGCGC.4.240424_A01052_0193_BH7JMMDRX5.L2400250"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES530H895X4WA3NQ6CY2QV",
#     #           "libraryId": "L2400251",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES530355YNZ3VHQQQ204PF",
#     #           "sampleId": "PRJ240561",
#     #           "externalSampleId": "4-218-004_Bx",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES51WC4GV5YDJNTMAK2YY1",
#     #           "subjectId": "218-004"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #             "projectId": "BPOP-retro",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400251",
#     #             "index": "GCCCAGTG",
#     #             "index2": "CCGCAATT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GCCCAGTG.CCGCAATT.4.240424_A01052_0193_BH7JMMDRX5.L2400251"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#     #           "libraryId": "L2400252",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES531H420JM9MG5R4AE1AZ",
#     #           "sampleId": "PRJ240562",
#     #           "externalSampleId": "5-218-004_04",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES51WC4GV5YDJNTMAK2YY1",
#     #           "subjectId": "218-004"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #             "projectId": "BPOP-retro",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400252",
#     #             "index": "TGACAGCT",
#     #             "index2": "CCCGTAGG",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "TGACAGCT.CCCGTAGG.4.240424_A01052_0193_BH7JMMDRX5.L2400252"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#     #           "libraryId": "L2400253",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES532ZBHWY3DWY0DWQ223R",
#     #           "sampleId": "PRJ240566",
#     #           "externalSampleId": "9-218-007_Bx",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES522WN7YPZS1Z9NGSPNDA",
#     #           "subjectId": "218-007"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #             "projectId": "BPOP-retro",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400253",
#     #             "index": "CATCACCC",
#     #             "index2": "ATATAGCA",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "CATCACCC.ATATAGCA.4.240424_A01052_0193_BH7JMMDRX5.L2400253"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES534XGBFYDVYV8ZG6SYS0",
#     #           "libraryId": "L2400254",
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "borderline",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES534BX7B89X5EKSCFRDDZ",
#     #           "sampleId": "PRJ240567",
#     #           "externalSampleId": "10-218-007_04",
#     #           "source": "tissue"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES522WN7YPZS1Z9NGSPNDA",
#     #           "subjectId": "218-007"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #             "projectId": "BPOP-retro",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400254",
#     #             "index": "CTGGAGTA",
#     #             "index2": "GTTCGGTT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "CTGGAGTA.GTTCGGTT.4.240424_A01052_0193_BH7JMMDRX5.L2400254"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#     #           "libraryId": "L2400255",
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "very-poor",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES535VGG93023KWAFMWGH4",
#     #           "sampleId": "PRJ240200",
#     #           "externalSampleId": "RNA036747",
#     #           "source": "FFPE"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#     #           "subjectId": "SN_PMC-141"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #             "projectId": "CUP",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400255",
#     #             "index": "GATCCGGG",
#     #             "index2": "AAGCAGGT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GATCCGGG.AAGCAGGT.4.240424_A01052_0193_BH7JMMDRX5.L2400255"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES537S0W1AX9PQPST13GM9",
#     #           "libraryId": "L2400256",
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "very-poor",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES5379C40K08YG3JDMZJN7",
#     #           "sampleId": "PRJ240648",
#     #           "externalSampleId": "RNA037080",
#     #           "source": "FFPE"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES529GSPBV64SESK9SWD76",
#     #           "subjectId": "SN_PMC-145"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #             "projectId": "CUP",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400256",
#     #             "index": "AACACCTG",
#     #             "index2": "CGCATGGG",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "AACACCTG.CGCATGGG.4.240424_A01052_0193_BH7JMMDRX5.L2400256"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "orcabusId": "lib.01J8ES5395KETT9T2NJSVNDKNP",
#     #           "libraryId": "L2400257",
#     #           "phenotype": "negative-control",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 0.1
#     #         },
#     #         "sample": {
#     #           "orcabusId": "smp.01J8ES538PFF6MQQ35PTC00JAY",
#     #           "sampleId": "NTC_NebRNA240226",
#     #           "externalSampleId": "NTC_NebRNA240226",
#     #           "source": "water"
#     #         },
#     #         "subject": {
#     #           "orcabusId": "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#     #           "subjectId": "negative control"
#     #         },
#     #         "projectSet": [
#     #           {
#     #             "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #             "projectId": "Control",
#     #             "name": null,
#     #             "description": null
#     #           }
#     #         ],
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400257",
#     #             "index": "GTGACGTT",
#     #             "index2": "TCCCAGAT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ],
#     #         "fastqListRows": [
#     #           {
#     #             "fastqListRowRgid": "GTGACGTT.TCCCAGAT.4.240424_A01052_0193_BH7JMMDRX5.L2400257"
#     #           }
#     #         ]
#     #       }
#     #     }
#     #   ],
#     #   "library_set": [
#     #     "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#     #     "lib.01J8ES530H895X4WA3NQ6CY2QV",
#     #     "lib.01J8ES534XGBFYDVYV8ZG6SYS0",
#     #     "lib.01J8ES4MPZ5B201R50K42XXM4M",
#     #     "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#     #     "lib.01J8ES4Y5D52202JVBXHJ9Q9WF",
#     #     "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9",
#     #     "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#     #     "lib.01J8ES52XYMVGRB1Q458THNG4T",
#     #     "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#     #     "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#     #     "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#     #     "lib.01J8ES4ZST489C712CG3R9NQSQ",
#     #     "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#     #     "lib.01J8ES537S0W1AX9PQPST13GM9",
#     #     "lib.01J8ES52C3N585BGGY4VNXHC83",
#     #     "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#     #     "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#     #     "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#     #     "lib.01J8ES51V0RSVT6C7WQR72QQED",
#     #     "lib.01J8ES52889Q8826P5SH9HDPP0",
#     #     "lib.01J8ES5395KETT9T2NJSVNDKNP",
#     #     "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#     #     "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#     #     "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#     #     "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#     #     "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#     #     "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#     #     "lib.01J8ES4XQG3MPBW94TTVT4STVG"
#     #   ],
#     #   "subject_set": [
#     #     "sbj.01J8ES4XKHKNQ1NF8EKKACZ032",
#     #     "sbj.01J8ES4ZEQ3FVD6DDVEG8MW60Q",
#     #     "sbj.01J8ES51S87R4EJ61QJ0DMDYWZ",
#     #     "sbj.01J8ES4DRJ31Z2H1GJQZGVDXZR",
#     #     "sbj.01J8ES4MNXJSDRR406DAXFZP2N",
#     #     "sbj.01J8ES4GNVGZSJVTHGVKS9VW7F",
#     #     "sbj.01J8ES51WC4GV5YDJNTMAK2YY1",
#     #     "sbj.01J8ES4ZCKNW6QKP006SYNZ5RA",
#     #     "sbj.01J8ES522WN7YPZS1Z9NGSPNDA",
#     #     "sbj.01J8ES4DFMNF0SX6P8P8Y9J6K1",
#     #     "sbj.01J8ES4XW2TXGEJBQWCVMRZRTS",
#     #     "sbj.01J8ES529GSPBV64SESK9SWD76",
#     #     "sbj.01J8ES4FNJ2FCAK0RJST0428X0"
#     #   ],
#     #   "project_set": [
#     #     "prj.01J8ES4FC6DVW20AR33FBX2SA8",
#     #     "prj.01J8ES4FH3XMPZQNDJ9J000BXX",
#     #     "prj.01J8ES4EZAA5YMHX82664GJQB3",
#     #     "prj.01J8ES4EBXK08WDWB97BSCX1C9",
#     #     "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B",
#     #     "prj.01J8ES4XMWD0DH7MDRNER5TZS1"
#     #   ],
#     #   "sample_set": [
#     #     "smp.01J8ES5379C40K08YG3JDMZJN7",
#     #     "smp.01J8ES4XWXFANT7P0T3AFXA85G",
#     #     "smp.01J8ES4Y0V0ZBKAE91TDSY0BBB",
#     #     "smp.01J8ES535VGG93023KWAFMWGH4",
#     #     "smp.01J8ES4FP9WTFBDNGKVG3D9BD4",
#     #     "smp.01J8ES52EEX67YRYAJS3F5GMJ5",
#     #     "smp.01J8ES4XYTSVQVRSBA9M26NSZY",
#     #     "smp.01J8ES4ZMETZP255WMFC8TSCYT",
#     #     "smp.01J8ES51T84KVVVSEPYQFGW0EV",
#     #     "smp.01J8ES538PFF6MQQ35PTC00JAY",
#     #     "smp.01J8ES4XMDW0FV1YMWHSZZQ4TX",
#     #     "smp.01J8ES52D076FQM5K8128AQ593",
#     #     "smp.01J8ES4Y37JTPEEJSED9BXH8N2",
#     #     "smp.01J8ES4ZQ76H8P0Q7S618F3BMA",
#     #     "smp.01J8ES4Y4XK1WX4WCPD6XY8KNM",
#     #     "smp.01J8ES531H420JM9MG5R4AE1AZ",
#     #     "smp.01J8ES534BX7B89X5EKSCFRDDZ",
#     #     "smp.01J8ES4ZNT47EM37QKMT12JPPJ",
#     #     "smp.01J8ES4MPHSX7MRCTTFWJBYTT7",
#     #     "smp.01J8ES52A5QX0GQ6RB78Z8DGYQ",
#     #     "smp.01J8ES532ZBHWY3DWY0DWQ223R",
#     #     "smp.01J8ES4ZVAR9NQM55Z2TXCDY9V",
#     #     "smp.01J8ES4XRG9NB38N03688M2CCB",
#     #     "smp.01J8ES527QKB5Y5RVZWZ8HQX0H",
#     #     "smp.01J8ES530355YNZ3VHQQQ204PF",
#     #     "smp.01J8ES4ZDAFRK3K3PY33F8XS0W",
#     #     "smp.01J8ES52BM8BVS3PX47E6FM7D5",
#     #     "smp.01J8ES52XE661E8V8XTWD02QCK",
#     #     "smp.01J8ES4XQ071BF3WZN111SNJ2B"
#     #   ]
#     # }