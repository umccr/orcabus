#!/usr/bin/env python3

"""
Generate event data objects

Given an instrument run id, samplesheet, library_obj_list, specimen_obj_list, subject_obj_list,
Generate the events for

* Start of the SampleSheet Shower
* Subject Event Data Objects (subject id, plus event data)
* Library Event Data Objects (library id, plus event data)
* End of the SampleSheet Shower
"""
from typing import Dict, List


def generate_subject_event_data_object_from_subject(subject_obj: Dict, instrument_run_id: str) -> Dict:
    return {
        "event_data": {
            "instrumentRunId": instrument_run_id,
            "subject": {
                "orcabusId": subject_obj.get("orcabus_id"),
                "subjectId": subject_obj.get("subject_id")
            }
        }
    }


def get_specimen_obj_from_library_obj(library_obj: Dict, specimen_obj_list: List[Dict]) -> Dict:
    """
    Given a list of specimen objects, filter
    :param library_obj:
    :param specimen_obj_list:
    :return:
    """
    return next(
        filter(
            lambda specimen_object_iter: specimen_object_iter.get("id") == library_obj.get("specimen"),
            specimen_obj_list
        )
    )


def get_subject_obj_from_specimen_obj(specimen_obj: Dict, subject_obj_list: List[Dict]) -> Dict:
    """
    Given a specimen object, return the subject id
    :param specimen_obj:
    :param subject_obj_list:
    :return:
    """
    return next(
        filter(
            lambda subject_obj_iter: subject_obj_iter.get("id") == specimen_obj.get("subject"),
            subject_obj_list
        )
    )


def get_library_bclconvert_rows(library_obj: Dict, bclconvert_data: List[Dict]) -> List[Dict]:
    """
    Get library bclconvert rows
    :param library_obj:
    :param bclconvert_data:
    :return:
    """
    return list(
        filter(
            lambda bclconvert_row: bclconvert_row.get("sample_id") == library_obj.get("library_id"),
            bclconvert_data
        )
    )


def generate_library_event_data_object_from_library_specimen_and_subject(
        library_obj: Dict,
        instrument_run_id: str,
        specimen_obj: Dict,
        subject_obj: Dict,
        bclconvert_rows: List[Dict]
) -> Dict:
    """
    Generate library event data object from library specimen and subject
    :param library_obj:
    :param instrument_run_id:
    :param specimen_obj:
    :param subject_obj:
    :param bclconvert_rows:
    :return:
    """

    library_event_obj = {
        "orcabusId": library_obj.get("orcabus_id"),
        "libraryId": library_obj.get("library_id"),
        "phenotype": library_obj.get("phenotype", None),
        "workflow": library_obj.get("workflow", None),
        "quality": library_obj.get("quality", None),
        "type": library_obj.get("type", None),
        "assay": library_obj.get("assay", None),
        "coverage": library_obj.get("coverage", None),
        "projectOwner": library_obj.get("project_owner", None),
        "projectName": library_obj.get("project_name", None),
        "specimen": {
            "orcabusId": specimen_obj.get("orcabus_id"),
            "specimenId": specimen_obj.get("specimen_id")
        },
        "subject": {
            "orcabusId": subject_obj.get("orcabus_id"),
            "subjectId": subject_obj.get("subject_id")
        }
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

    return {
        "id": library_obj.get("id"),
        "event_data": {
            "instrumentRunId": instrument_run_id,
            "library": library_event_obj,
            "bclconvertDataRows": bclconvert_data_rows_event_obj
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

    # Get the specimen object list
    specimen_obj_list = event['specimen_obj_list']

    # Get the subject object list
    subject_obj_list = event['subject_obj_list']

    # For each subject, generate the subject event data object
    subject_event_data_list = list(
        map(
            lambda subject_obj_iter: (
                generate_subject_event_data_object_from_subject(subject_obj_iter, instrument_run_id)
            ),
            subject_obj_list
        )
    )

    library_event_data_list = []

    for library_obj in library_obj_list:
        # Get the bclconvert data rows
        bclconvert_rows = get_library_bclconvert_rows(library_obj, samplesheet['bclconvert_data'])

        # Get the specimen object
        specimen_obj = get_specimen_obj_from_library_obj(library_obj, specimen_obj_list)

        # Get the subject object
        subject_obj = get_subject_obj_from_specimen_obj(specimen_obj, subject_obj_list)

        # Generate the library event data object
        library_event_data_list.append(
            generate_library_event_data_object_from_library_specimen_and_subject(
                library_obj,
                instrument_run_id,
                specimen_obj,
                subject_obj,
                bclconvert_rows
            )
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
        "subject_event_data_list": subject_event_data_list,
        "library_event_data_list": library_event_data_list
    }

# if __name__ == "__main__":
#     import json
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
#                             "id": 10723,
#                             "internal_id": "L2400102",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "borderline",
#                             "type": "WGS",
#                             "assay": "ctTSO",
#                             "coverage": 50.0,
#                             "specimen": 4077
#                         },
#                         {
#                             "id": 10830,
#                             "internal_id": "L2400159",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6,
#                             "specimen": 9195
#                         },
#                         {
#                             "id": 10831,
#                             "internal_id": "L2400160",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6,
#                             "specimen": 9196
#                         },
#                         {
#                             "id": 10832,
#                             "internal_id": "L2400161",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6,
#                             "specimen": 9197
#                         },
#                         {
#                             "id": 10833,
#                             "internal_id": "L2400162",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6,
#                             "specimen": 9198
#                         },
#                         {
#                             "id": 10834,
#                             "internal_id": "L2400163",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6,
#                             "specimen": 9199
#                         },
#                         {
#                             "id": 10835,
#                             "internal_id": "L2400164",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6,
#                             "specimen": 9200
#                         },
#                         {
#                             "id": 10836,
#                             "internal_id": "L2400165",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6,
#                             "specimen": 9201
#                         },
#                         {
#                             "id": 10837,
#                             "internal_id": "L2400166",
#                             "phenotype": "negative-control",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 0.1,
#                             "specimen": 9202
#                         },
#                         {
#                             "id": 10862,
#                             "internal_id": "L2400191",
#                             "phenotype": "normal",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40.0,
#                             "specimen": 9216
#                         },
#                         {
#                             "id": 10866,
#                             "internal_id": "L2400195",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0,
#                             "specimen": 9220
#                         },
#                         {
#                             "id": 10867,
#                             "internal_id": "L2400196",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0,
#                             "specimen": 9221
#                         },
#                         {
#                             "id": 10868,
#                             "internal_id": "L2400197",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0,
#                             "specimen": 9222
#                         },
#                         {
#                             "id": 10869,
#                             "internal_id": "L2400198",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80.0,
#                             "specimen": 9223
#                         },
#                         {
#                             "id": 10902,
#                             "internal_id": "L2400231",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "poor",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 100.0,
#                             "specimen": 9242
#                         },
#                         {
#                             "id": 10909,
#                             "internal_id": "L2400238",
#                             "phenotype": "normal",
#                             "workflow": "clinical",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40.0,
#                             "specimen": 9249
#                         },
#                         {
#                             "id": 10910,
#                             "internal_id": "L2400239",
#                             "phenotype": "normal",
#                             "workflow": "clinical",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40.0,
#                             "specimen": 9250
#                         },
#                         {
#                             "id": 10911,
#                             "internal_id": "L2400240",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "poor",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 100.0,
#                             "specimen": 9251
#                         },
#                         {
#                             "id": 10912,
#                             "internal_id": "L2400241",
#                             "phenotype": "negative-control",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 0.1,
#                             "specimen": 9252
#                         },
#                         {
#                             "id": 10913,
#                             "internal_id": "L2400242",
#                             "phenotype": "normal",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 15.0,
#                             "specimen": 9253
#                         },
#                         {
#                             "id": 10920,
#                             "internal_id": "L2400249",
#                             "phenotype": "tumor",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 1.0,
#                             "specimen": 9260
#                         },
#                         {
#                             "id": 10921,
#                             "internal_id": "L2400250",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0,
#                             "specimen": 9079
#                         },
#                         {
#                             "id": 10922,
#                             "internal_id": "L2400251",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0,
#                             "specimen": 9261
#                         },
#                         {
#                             "id": 10923,
#                             "internal_id": "L2400252",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0,
#                             "specimen": 9262
#                         },
#                         {
#                             "id": 10924,
#                             "internal_id": "L2400253",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0,
#                             "specimen": 9263
#                         },
#                         {
#                             "id": 10925,
#                             "internal_id": "L2400254",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "borderline",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0,
#                             "specimen": 9264
#                         },
#                         {
#                             "id": 10926,
#                             "internal_id": "L2400255",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "very-poor",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0,
#                             "specimen": 9265
#                         },
#                         {
#                             "id": 10927,
#                             "internal_id": "L2400256",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "very-poor",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6.0,
#                             "specimen": 9266
#                         },
#                         {
#                             "id": 10928,
#                             "internal_id": "L2400257",
#                             "phenotype": "negative-control",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 0.1,
#                             "specimen": 9267
#                         }
#                     ],
#                     "specimen_obj_list": [
#                         {
#                             "id": 4077,
#                             "internal_id": "MDX210402",
#                             "source": "plasma-serum",
#                             "subject": 1272
#                         },
#                         {
#                             "id": 9079,
#                             "internal_id": "PRJ240003",
#                             "source": "tissue",
#                             "subject": 3984
#                         },
#                         {
#                             "id": 9195,
#                             "internal_id": "PTC_SCMM1pc2",
#                             "source": "cfDNA",
#                             "subject": 3903
#                         },
#                         {
#                             "id": 9196,
#                             "internal_id": "PTC_SCMM1pc3",
#                             "source": "cfDNA",
#                             "subject": 3903
#                         },
#                         {
#                             "id": 9197,
#                             "internal_id": "PTC_SCMM1pc4",
#                             "source": "cfDNA",
#                             "subject": 3903
#                         },
#                         {
#                             "id": 9198,
#                             "internal_id": "PTC_SCMM01pc20",
#                             "source": "cfDNA",
#                             "subject": 4143
#                         },
#                         {
#                             "id": 9199,
#                             "internal_id": "PTC_SCMM01pc15",
#                             "source": "cfDNA",
#                             "subject": 4143
#                         },
#                         {
#                             "id": 9200,
#                             "internal_id": "PTC_SCMM01pc10",
#                             "source": "cfDNA",
#                             "subject": 4143
#                         },
#                         {
#                             "id": 9201,
#                             "internal_id": "PTC_SCMM01pc5",
#                             "source": "cfDNA",
#                             "subject": 4143
#                         },
#                         {
#                             "id": 9202,
#                             "internal_id": "NTC_v2ctTSO240207",
#                             "source": "water",
#                             "subject": 58
#                         },
#                         {
#                             "id": 9216,
#                             "internal_id": "PRJ240169",
#                             "source": "blood",
#                             "subject": 4148
#                         },
#                         {
#                             "id": 9220,
#                             "internal_id": "PRJ240180",
#                             "source": "tissue",
#                             "subject": 4148
#                         },
#                         {
#                             "id": 9221,
#                             "internal_id": "PRJ240181",
#                             "source": "tissue",
#                             "subject": 4148
#                         },
#                         {
#                             "id": 9222,
#                             "internal_id": "PRJ240182",
#                             "source": "tissue",
#                             "subject": 4149
#                         },
#                         {
#                             "id": 9223,
#                             "internal_id": "PRJ240183",
#                             "source": "tissue",
#                             "subject": 4149
#                         },
#                         {
#                             "id": 9242,
#                             "internal_id": "PRJ240199",
#                             "source": "FFPE",
#                             "subject": 4152
#                         },
#                         {
#                             "id": 9249,
#                             "internal_id": "PRJ240643",
#                             "source": "blood",
#                             "subject": 4152
#                         },
#                         {
#                             "id": 9250,
#                             "internal_id": "PRJ240646",
#                             "source": "blood",
#                             "subject": 4155
#                         },
#                         {
#                             "id": 9251,
#                             "internal_id": "PRJ240647",
#                             "source": "FFPE",
#                             "subject": 4155
#                         },
#                         {
#                             "id": 9252,
#                             "internal_id": "NTC_TSqN240226",
#                             "source": "water",
#                             "subject": 58
#                         },
#                         {
#                             "id": 9253,
#                             "internal_id": "PTC_TSqN240226",
#                             "source": "cell-line",
#                             "subject": 104
#                         },
#                         {
#                             "id": 9260,
#                             "internal_id": "PTC_NebRNA240226",
#                             "source": "cell-line",
#                             "subject": 57
#                         },
#                         {
#                             "id": 9261,
#                             "internal_id": "PRJ240561",
#                             "source": "tissue",
#                             "subject": 4153
#                         },
#                         {
#                             "id": 9262,
#                             "internal_id": "PRJ240562",
#                             "source": "tissue",
#                             "subject": 4153
#                         },
#                         {
#                             "id": 9263,
#                             "internal_id": "PRJ240566",
#                             "source": "tissue",
#                             "subject": 4154
#                         },
#                         {
#                             "id": 9264,
#                             "internal_id": "PRJ240567",
#                             "source": "tissue",
#                             "subject": 4154
#                         },
#                         {
#                             "id": 9265,
#                             "internal_id": "PRJ240200",
#                             "source": "FFPE",
#                             "subject": 4152
#                         },
#                         {
#                             "id": 9266,
#                             "internal_id": "PRJ240648",
#                             "source": "FFPE",
#                             "subject": 4155
#                         },
#                         {
#                             "id": 9267,
#                             "internal_id": "NTC_NebRNA240226",
#                             "source": "water",
#                             "subject": 58
#                         }
#                     ],
#                     "subject_obj_list": [
#                         {
#                             "id": 57,
#                             "internal_id": "SBJ00029"
#                         },
#                         {
#                             "id": 58,
#                             "internal_id": "SBJ00006"
#                         },
#                         {
#                             "id": 104,
#                             "internal_id": "SBJ00005"
#                         },
#                         {
#                             "id": 1272,
#                             "internal_id": "SBJ01143"
#                         },
#                         {
#                             "id": 3903,
#                             "internal_id": "SBJ04407"
#                         },
#                         {
#                             "id": 3984,
#                             "internal_id": "SBJ04488"
#                         },
#                         {
#                             "id": 4143,
#                             "internal_id": "SBJ04648"
#                         },
#                         {
#                             "id": 4148,
#                             "internal_id": "SBJ04653"
#                         },
#                         {
#                             "id": 4149,
#                             "internal_id": "SBJ04654"
#                         },
#                         {
#                             "id": 4152,
#                             "internal_id": "SBJ04659"
#                         },
#                         {
#                             "id": 4153,
#                             "internal_id": "SBJ04660"
#                         },
#                         {
#                             "id": 4154,
#                             "internal_id": "SBJ04661"
#                         },
#                         {
#                             "id": 4155,
#                             "internal_id": "SBJ04662"
#                         }
#                     ]
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
#     #   "subject_event_data_list": [
#     #     {
#     #       "id": 57,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 57,
#     #           "internalId": "SBJ00029"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 58,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 58,
#     #           "internalId": "SBJ00006"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 104,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 104,
#     #           "internalId": "SBJ00005"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 1272,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 1272,
#     #           "internalId": "SBJ01143"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 3903,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 3903,
#     #           "internalId": "SBJ04407"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 3984,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 3984,
#     #           "internalId": "SBJ04488"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 4143,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 4143,
#     #           "internalId": "SBJ04648"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 4148,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 4148,
#     #           "internalId": "SBJ04653"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 4149,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 4149,
#     #           "internalId": "SBJ04654"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 4152,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 4152,
#     #           "internalId": "SBJ04659"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 4153,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 4153,
#     #           "internalId": "SBJ04660"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 4154,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 4154,
#     #           "internalId": "SBJ04661"
#     #         }
#     #       }
#     #     },
#     #     {
#     #       "id": 4155,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "subject": {
#     #           "id": 4155,
#     #           "internalId": "SBJ04662"
#     #         }
#     #       }
#     #     }
#     #   ],
#     #   "library_event_data_list": [
#     #     {
#     #       "id": 10723,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10723,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "borderline",
#     #           "type": "WGS",
#     #           "assay": "ctTSO",
#     #           "coverage": 50.0,
#     #           "specimen": 4077
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400102",
#     #             "index": "GAATTCGT",
#     #             "index2": "TTATGAGT",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10830,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10830,
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6,
#     #           "specimen": 9195
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400159",
#     #             "index": "GAGAATGGTT",
#     #             "index2": "TTGCTGCCGA",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10831,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10831,
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6,
#     #           "specimen": 9196
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400160",
#     #             "index": "AGAGGCAACC",
#     #             "index2": "CCATCATTAG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10832,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10832,
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6,
#     #           "specimen": 9197
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400161",
#     #             "index": "CCATCATTAG",
#     #             "index2": "AGAGGCAACC",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10833,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10833,
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6,
#     #           "specimen": 9198
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400162",
#     #             "index": "GATAGGCCGA",
#     #             "index2": "GCCATGTGCG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10834,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10834,
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6,
#     #           "specimen": 9199
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400163",
#     #             "index": "ATGGTTGACT",
#     #             "index2": "AGGACAGGCC",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10835,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10835,
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6,
#     #           "specimen": 9200
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400164",
#     #             "index": "TATTGCGCTC",
#     #             "index2": "CCTAACACAG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10836,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10836,
#     #           "phenotype": "tumor",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 38.6,
#     #           "specimen": 9201
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400165",
#     #             "index": "ACGCCTTGTT",
#     #             "index2": "ACGTTCCTTA",
#     #             "lane": 4,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10837,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10837,
#     #           "phenotype": "negative-control",
#     #           "workflow": "manual",
#     #           "quality": "good",
#     #           "type": "ctDNA",
#     #           "assay": "ctTSOv2",
#     #           "coverage": 0.1,
#     #           "specimen": 9202
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400166",
#     #             "index": "TTCTACATAC",
#     #             "index2": "TTACAGTTAG",
#     #             "lane": 1,
#     #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10862,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10862,
#     #           "phenotype": "normal",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 40.0,
#     #           "specimen": 9216
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400191",
#     #             "index": "GCACGGAC",
#     #             "index2": "TGCGAGAC",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10866,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10866,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0,
#     #           "specimen": 9220
#     #         },
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
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10867,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10867,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0,
#     #           "specimen": 9221
#     #         },
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
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10868,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10868,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0,
#     #           "specimen": 9222
#     #         },
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
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10869,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10869,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 80.0,
#     #           "specimen": 9223
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400198",
#     #             "index": "CTTGGTAT",
#     #             "index2": "GGACTTGG",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10902,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10902,
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "poor",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 100.0,
#     #           "specimen": 9242
#     #         },
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
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10909,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10909,
#     #           "phenotype": "normal",
#     #           "workflow": "clinical",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 40.0,
#     #           "specimen": 9249
#     #         },
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
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10910,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10910,
#     #           "phenotype": "normal",
#     #           "workflow": "clinical",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 40.0,
#     #           "specimen": 9250
#     #         },
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
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10911,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10911,
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "poor",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 100.0,
#     #           "specimen": 9251
#     #         },
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
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10912,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10912,
#     #           "phenotype": "negative-control",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 0.1,
#     #           "specimen": 9252
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400241",
#     #             "index": "GTTCCAAT",
#     #             "index2": "GCAGAATT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10913,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10913,
#     #           "phenotype": "normal",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WGS",
#     #           "assay": "TsqNano",
#     #           "coverage": 15.0,
#     #           "specimen": 9253
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400242",
#     #             "index": "ACCTTGGC",
#     #             "index2": "ATGAGGCC",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10920,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10920,
#     #           "phenotype": "tumor",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 1.0,
#     #           "specimen": 9260
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400249",
#     #             "index": "AGTTTCGA",
#     #             "index2": "CCTACGAT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10921,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10921,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0,
#     #           "specimen": 9079
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400250",
#     #             "index": "GAACCTCT",
#     #             "index2": "GTCTGCGC",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10922,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10922,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0,
#     #           "specimen": 9261
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400251",
#     #             "index": "GCCCAGTG",
#     #             "index2": "CCGCAATT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10923,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10923,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0,
#     #           "specimen": 9262
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400252",
#     #             "index": "TGACAGCT",
#     #             "index2": "CCCGTAGG",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10924,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10924,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0,
#     #           "specimen": 9263
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400253",
#     #             "index": "CATCACCC",
#     #             "index2": "ATATAGCA",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10925,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10925,
#     #           "phenotype": "tumor",
#     #           "workflow": "research",
#     #           "quality": "borderline",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0,
#     #           "specimen": 9264
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400254",
#     #             "index": "CTGGAGTA",
#     #             "index2": "GTTCGGTT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10926,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10926,
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "very-poor",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0,
#     #           "specimen": 9265
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400255",
#     #             "index": "GATCCGGG",
#     #             "index2": "AAGCAGGT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10927,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10927,
#     #           "phenotype": "tumor",
#     #           "workflow": "clinical",
#     #           "quality": "very-poor",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 6.0,
#     #           "specimen": 9266
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400256",
#     #             "index": "AACACCTG",
#     #             "index2": "CGCATGGG",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     },
#     #     {
#     #       "id": 10928,
#     #       "event_data": {
#     #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #         "library": {
#     #           "id": 10928,
#     #           "phenotype": "negative-control",
#     #           "workflow": "control",
#     #           "quality": "good",
#     #           "type": "WTS",
#     #           "assay": "NebRNA",
#     #           "coverage": 0.1,
#     #           "specimen": 9267
#     #         },
#     #         "bclconvertDataRows": [
#     #           {
#     #             "sampleId": "L2400257",
#     #             "index": "GTGACGTT",
#     #             "index2": "TCCCAGAT",
#     #             "lane": 4,
#     #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
#     #           }
#     #         ]
#     #       }
#     #     }
#     #   ]
#     # }
