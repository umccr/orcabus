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
                "orcabusId": subject_obj.get("orcabusId"),
                "subjectId": subject_obj.get("subjectId")
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
            lambda specimen_object_iter: specimen_object_iter.get("orcabusId") == library_obj.get("specimen"),
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
            lambda subject_obj_iter: subject_obj_iter.get("orcabusId") == specimen_obj.get("subject"),
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
            lambda bclconvert_row: bclconvert_row.get("sample_id") == library_obj.get("libraryId"),
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
        "orcabusId": library_obj.get("orcabusId"),
        "libraryId": library_obj.get("libraryId"),
        "phenotype": library_obj.get("phenotype", None),
        "workflow": library_obj.get("workflow", None),
        "quality": library_obj.get("quality", None),
        "type": library_obj.get("type", None),
        "assay": library_obj.get("assay", None),
        "coverage": library_obj.get("coverage", None),
        "projectOwner": library_obj.get("projectOwner", None),
        "projectName": library_obj.get("projectName", None),
        "specimen": {
            "orcabusId": specimen_obj.get("orcabusId"),
            "specimenId": specimen_obj.get("specimenId")
        },
        "subject": {
            "orcabusId": subject_obj.get("orcabusId"),
            "subjectId": subject_obj.get("subjectId")
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
            "bclconvertDataRows": bclconvert_data_rows_event_obj,
            "fastqListRows": fastq_list_row_ids
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

    # Generate project data level events
    project_list = list(
        set(
            map(
                lambda library_iter: (
                    library_iter.get("projectOwner"), library_iter.get("projectName")
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
                                "orcabusId": library_obj_iter.get("orcabusId"),
                                "libraryId": library_obj_iter.get("libraryId")
                            },
                            filter(
                                lambda library_obj_iter: (
                                        library_obj_iter.get("projectOwner") == project_owner and
                                        library_obj_iter.get("projectName") == project_name
                                ),
                                library_obj_list
                            )
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
        "subject_event_data_list": subject_event_data_list,
        "library_event_data_list": library_event_data_list
    }


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            handler(
                {
                    "instrument_run_id": "240424_A01052_0193_BH7JMMDRX5",
                    "samplesheet":
                        {
                            "header": {
                                "file_format_version": 2,
                                "run_name": "Tsqn240214-26-ctTSOv2_29Feb24",
                                "instrument_type": "NovaSeq"
                            },
                            "reads": {
                                "read_1_cycles": 151,
                                "read_2_cycles": 151,
                                "index_1_cycles": 10,
                                "index_2_cycles": 10
                            },
                            "bclconvert_settings": {
                                "minimum_trimmed_read_length": 35,
                                "minimum_adapter_overlap": 3,
                                "mask_short_reads": 35,
                                "software_version": "4.2.7"
                            },
                            "bclconvert_data": [
                                {
                                    "lane": 1,
                                    "sample_id": "L2400102",
                                    "index": "GAATTCGT",
                                    "index2": "TTATGAGT",
                                    "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
                                },
                                {
                                    "lane": 1,
                                    "sample_id": "L2400159",
                                    "index": "GAGAATGGTT",
                                    "index2": "TTGCTGCCGA",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 1,
                                    "sample_id": "L2400160",
                                    "index": "AGAGGCAACC",
                                    "index2": "CCATCATTAG",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 1,
                                    "sample_id": "L2400161",
                                    "index": "CCATCATTAG",
                                    "index2": "AGAGGCAACC",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 1,
                                    "sample_id": "L2400162",
                                    "index": "GATAGGCCGA",
                                    "index2": "GCCATGTGCG",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 1,
                                    "sample_id": "L2400163",
                                    "index": "ATGGTTGACT",
                                    "index2": "AGGACAGGCC",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 1,
                                    "sample_id": "L2400164",
                                    "index": "TATTGCGCTC",
                                    "index2": "CCTAACACAG",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 1,
                                    "sample_id": "L2400166",
                                    "index": "TTCTACATAC",
                                    "index2": "TTACAGTTAG",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 2,
                                    "sample_id": "L2400195",
                                    "index": "ATGAGGCC",
                                    "index2": "CAATTAAC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 2,
                                    "sample_id": "L2400196",
                                    "index": "ACTAAGAT",
                                    "index2": "CCGCGGTT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 2,
                                    "sample_id": "L2400197",
                                    "index": "GTCGGAGC",
                                    "index2": "TTATAACC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 2,
                                    "sample_id": "L2400231",
                                    "index": "TCGTAGTG",
                                    "index2": "CCAAGTCT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 2,
                                    "sample_id": "L2400238",
                                    "index": "GGAGCGTC",
                                    "index2": "GCACGGAC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 2,
                                    "sample_id": "L2400239",
                                    "index": "ATGGCATG",
                                    "index2": "GGTACCTT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 2,
                                    "sample_id": "L2400240",
                                    "index": "GCAATGCA",
                                    "index2": "AACGTTCC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 3,
                                    "sample_id": "L2400195",
                                    "index": "ATGAGGCC",
                                    "index2": "CAATTAAC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 3,
                                    "sample_id": "L2400196",
                                    "index": "ACTAAGAT",
                                    "index2": "CCGCGGTT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 3,
                                    "sample_id": "L2400197",
                                    "index": "GTCGGAGC",
                                    "index2": "TTATAACC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 3,
                                    "sample_id": "L2400231",
                                    "index": "TCGTAGTG",
                                    "index2": "CCAAGTCT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 3,
                                    "sample_id": "L2400238",
                                    "index": "GGAGCGTC",
                                    "index2": "GCACGGAC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 3,
                                    "sample_id": "L2400239",
                                    "index": "ATGGCATG",
                                    "index2": "GGTACCTT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 3,
                                    "sample_id": "L2400240",
                                    "index": "GCAATGCA",
                                    "index2": "AACGTTCC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400165",
                                    "index": "ACGCCTTGTT",
                                    "index2": "ACGTTCCTTA",
                                    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
                                    "adapter_read_1": "CTGTCTCTTATACACATCT",
                                    "adapter_read_2": "CTGTCTCTTATACACATCT"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400191",
                                    "index": "GCACGGAC",
                                    "index2": "TGCGAGAC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400197",
                                    "index": "GTCGGAGC",
                                    "index2": "TTATAACC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400198",
                                    "index": "CTTGGTAT",
                                    "index2": "GGACTTGG",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400241",
                                    "index": "GTTCCAAT",
                                    "index2": "GCAGAATT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400242",
                                    "index": "ACCTTGGC",
                                    "index2": "ATGAGGCC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400249",
                                    "index": "AGTTTCGA",
                                    "index2": "CCTACGAT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400250",
                                    "index": "GAACCTCT",
                                    "index2": "GTCTGCGC",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400251",
                                    "index": "GCCCAGTG",
                                    "index2": "CCGCAATT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400252",
                                    "index": "TGACAGCT",
                                    "index2": "CCCGTAGG",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400253",
                                    "index": "CATCACCC",
                                    "index2": "ATATAGCA",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400254",
                                    "index": "CTGGAGTA",
                                    "index2": "GTTCGGTT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400255",
                                    "index": "GATCCGGG",
                                    "index2": "AAGCAGGT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400256",
                                    "index": "AACACCTG",
                                    "index2": "CGCATGGG",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                },
                                {
                                    "lane": 4,
                                    "sample_id": "L2400257",
                                    "index": "GTGACGTT",
                                    "index2": "TCCCAGAT",
                                    "override_cycles": "Y151;I8N2;I8N2;Y151"
                                }
                            ],
                            "cloud_settings": {
                                "generated_version": "0.0.0",
                                "cloud_workflow": "ica_workflow_1",
                                "bclconvert_pipeline": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7"
                            },
                            "cloud_data": [
                                {
                                    "sample_id": "L2400102",
                                    "library_name": "L2400102_GAATTCGT_TTATGAGT",
                                    "library_prep_kit_name": "ctTSO"
                                },
                                {
                                    "sample_id": "L2400159",
                                    "library_name": "L2400159_GAGAATGGTT_TTGCTGCCGA",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400160",
                                    "library_name": "L2400160_AGAGGCAACC_CCATCATTAG",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400161",
                                    "library_name": "L2400161_CCATCATTAG_AGAGGCAACC",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400162",
                                    "library_name": "L2400162_GATAGGCCGA_GCCATGTGCG",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400163",
                                    "library_name": "L2400163_ATGGTTGACT_AGGACAGGCC",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400164",
                                    "library_name": "L2400164_TATTGCGCTC_CCTAACACAG",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400165",
                                    "library_name": "L2400165_ACGCCTTGTT_ACGTTCCTTA",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400166",
                                    "library_name": "L2400166_TTCTACATAC_TTACAGTTAG",
                                    "library_prep_kit_name": "ctTSOv2"
                                },
                                {
                                    "sample_id": "L2400191",
                                    "library_name": "L2400191_GCACGGAC_TGCGAGAC",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400195",
                                    "library_name": "L2400195_ATGAGGCC_CAATTAAC",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400196",
                                    "library_name": "L2400196_ACTAAGAT_CCGCGGTT",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400197",
                                    "library_name": "L2400197_GTCGGAGC_TTATAACC",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400198",
                                    "library_name": "L2400198_CTTGGTAT_GGACTTGG",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400231",
                                    "library_name": "L2400231_TCGTAGTG_CCAAGTCT",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400238",
                                    "library_name": "L2400238_GGAGCGTC_GCACGGAC",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400239",
                                    "library_name": "L2400239_ATGGCATG_GGTACCTT",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400240",
                                    "library_name": "L2400240_GCAATGCA_AACGTTCC",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400241",
                                    "library_name": "L2400241_GTTCCAAT_GCAGAATT",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400242",
                                    "library_name": "L2400242_ACCTTGGC_ATGAGGCC",
                                    "library_prep_kit_name": "TsqNano"
                                },
                                {
                                    "sample_id": "L2400249",
                                    "library_name": "L2400249_AGTTTCGA_CCTACGAT",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400250",
                                    "library_name": "L2400250_GAACCTCT_GTCTGCGC",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400251",
                                    "library_name": "L2400251_GCCCAGTG_CCGCAATT",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400252",
                                    "library_name": "L2400252_TGACAGCT_CCCGTAGG",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400253",
                                    "library_name": "L2400253_CATCACCC_ATATAGCA",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400254",
                                    "library_name": "L2400254_CTGGAGTA_GTTCGGTT",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400255",
                                    "library_name": "L2400255_GATCCGGG_AAGCAGGT",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400256",
                                    "library_name": "L2400256_AACACCTG_CGCATGGG",
                                    "library_prep_kit_name": "NebRNA"
                                },
                                {
                                    "sample_id": "L2400257",
                                    "library_name": "L2400257_GTGACGTT_TCCCAGAT",
                                    "library_prep_kit_name": "NebRNA"
                                }
                            ]
                        },
                    "library_obj_list": [
                        {
                            "orcabusId": "lib.01J5S9C4VMJ6PZ8GJ2G189AMXX",
                            "libraryId": "L2400102",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "borderline",
                            "type": "WGS",
                            "assay": "ctTSO",
                            "coverage": 50.0,
                            "projectOwner": "VCCC",
                            "projectName": "PO",
                            "specimen": "spc.01J5S9C4V269YTNA17TTP6NF76"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBG0NF8QBNVKM6ESCD60",
                            "libraryId": "L2400159",
                            "phenotype": "tumor",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 38.6,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBFDVZX7ZT3Y6TH28SY4"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBHP6NSB42RVFAP9PGJP",
                            "libraryId": "L2400160",
                            "phenotype": "tumor",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 38.6,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBH4V5B56CEJ5Q1XQKQ9"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBKCATYSFY40BRX6WJWX",
                            "libraryId": "L2400161",
                            "phenotype": "tumor",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 38.6,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBJTBJB72KJ74VSCHKJF"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBN6EAXW4AXG7TQ1H6NC",
                            "libraryId": "L2400162",
                            "phenotype": "tumor",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 38.6,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBMKTX5KN1XMPN479R2M"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBQFX8V1QRW7KAV3MD1W",
                            "libraryId": "L2400163",
                            "phenotype": "tumor",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 38.6,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBPSPN6S3TQCVJZF0XFE"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBS64DNTHK6CE850CCNZ",
                            "libraryId": "L2400164",
                            "phenotype": "tumor",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 38.6,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBRM3Y6PPF6E5NWZA7HG"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBTZRYQNTGAHPC2T601D",
                            "libraryId": "L2400165",
                            "phenotype": "tumor",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 38.6,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBTACFBNJKE8C523B0A7"
                        },
                        {
                            "orcabusId": "lib.01J5S9CBX10204CK7EKGTH9TMB",
                            "libraryId": "L2400166",
                            "phenotype": "negative-control",
                            "workflow": "manual",
                            "quality": "good",
                            "type": "ctDNA",
                            "assay": "ctTSOv2",
                            "coverage": 0.1,
                            "projectOwner": "UMCCR",
                            "projectName": "Testing",
                            "specimen": "spc.01J5S9CBWCGKQMG5S3ZSWA2ATE"
                        },
                        {
                            "orcabusId": "lib.01J5S9CDF8HHG5PJE3ECJMKMY7",
                            "libraryId": "L2400191",
                            "phenotype": "normal",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 40.0,
                            "projectOwner": "TJohn",
                            "projectName": "CAVATAK",
                            "specimen": "spc.01J5S9CDEH0ATXYAK52KW807R4"
                        },
                        {
                            "orcabusId": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S",
                            "libraryId": "L2400195",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 80.0,
                            "projectOwner": "TJohn",
                            "projectName": "CAVATAK",
                            "specimen": "spc.01J5S9CDQ0V9T98EGRPQJAP11S"
                        },
                        {
                            "orcabusId": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8",
                            "libraryId": "L2400196",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 80.0,
                            "projectOwner": "TJohn",
                            "projectName": "CAVATAK",
                            "specimen": "spc.01J5S9CDRZMMR9S784BYSMVWCT"
                        },
                        {
                            "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ",
                            "libraryId": "L2400197",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 80.0,
                            "projectOwner": "TJohn",
                            "projectName": "CAVATAK",
                            "specimen": "spc.01J5S9CDTSHGYMMJHE3SXEB2JG"
                        },
                        {
                            "orcabusId": "lib.01J5S9CDXCR7Q5K6A8VJRSMM4Q",
                            "libraryId": "L2400198",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 80.0,
                            "projectOwner": "TJohn",
                            "projectName": "CAVATAK",
                            "specimen": "spc.01J5S9CDWHAYG4RRG75GYZEK25"
                        },
                        {
                            "orcabusId": "lib.01J5S9CFX5P69S4KZRQGDFKV1N",
                            "libraryId": "L2400231",
                            "phenotype": "tumor",
                            "workflow": "clinical",
                            "quality": "poor",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 100.0,
                            "projectOwner": "Tothill",
                            "projectName": "CUP",
                            "specimen": "spc.01J5S9CFWAQTGK4MZB3HM5NVBC"
                        },
                        {
                            "orcabusId": "lib.01J5S9CGCAKQWHD9RBM9VXENY9",
                            "libraryId": "L2400238",
                            "phenotype": "normal",
                            "workflow": "clinical",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 40.0,
                            "projectOwner": "Tothill",
                            "projectName": "CUP",
                            "specimen": "spc.01J5S9CGBQCSQCS7XR3T89A82F"
                        },
                        {
                            "orcabusId": "lib.01J5S9CGEM1DHRQP72EP09B2TA",
                            "libraryId": "L2400239",
                            "phenotype": "normal",
                            "workflow": "clinical",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 40.0,
                            "projectOwner": "Tothill",
                            "projectName": "CUP",
                            "specimen": "spc.01J5S9CGE05BJCJ20M2KP4QWWB"
                        },
                        {
                            "orcabusId": "lib.01J5S9CGG9N9GH5879SY6A6BJB",
                            "libraryId": "L2400240",
                            "phenotype": "tumor",
                            "workflow": "clinical",
                            "quality": "poor",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 100.0,
                            "projectOwner": "Tothill",
                            "projectName": "CUP",
                            "specimen": "spc.01J5S9CGFQM3BQKADX8TWQ4ZH5"
                        },
                        {
                            "orcabusId": "lib.01J5S9CGJ6G09YQ9KFHPSXMMVD",
                            "libraryId": "L2400241",
                            "phenotype": "negative-control",
                            "workflow": "control",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 0.1,
                            "projectOwner": "UMCCR",
                            "projectName": "Control",
                            "specimen": "spc.01J5S9CGHK1G7YXD7C4FCXXS52"
                        },
                        {
                            "orcabusId": "lib.01J5S9CGKWDN7STKZKQM3KH9XR",
                            "libraryId": "L2400242",
                            "phenotype": "normal",
                            "workflow": "control",
                            "quality": "good",
                            "type": "WGS",
                            "assay": "TsqNano",
                            "coverage": 15.0,
                            "projectOwner": "UMCCR",
                            "projectName": "Control",
                            "specimen": "spc.01J5S9CGKAT4GHZ1VJFHVV15AD"
                        },
                        {
                            "orcabusId": "lib.01J5S9CH2SQ0P1SF7WAT5H4DSE",
                            "libraryId": "L2400249",
                            "phenotype": "tumor",
                            "workflow": "control",
                            "quality": "good",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 1.0,
                            "projectOwner": "UMCCR",
                            "projectName": "Control",
                            "specimen": "spc.01J5S9CH267XEJP5GMZK31MJWS"
                        },
                        {
                            "orcabusId": "lib.01J5S9CH4CYPA4SP05H8KRX4W9",
                            "libraryId": "L2400250",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 6.0,
                            "projectOwner": "Whittle",
                            "projectName": "BPOP-retro",
                            "specimen": "spc.01J5S9C0QC2TBZD7XA26D7WGTW"
                        },
                        {
                            "orcabusId": "lib.01J5S9CH65E4EE5QJEJ1C60GGG",
                            "libraryId": "L2400251",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 6.0,
                            "projectOwner": "Whittle",
                            "projectName": "BPOP-retro",
                            "specimen": "spc.01J5S9CH5KXY3VMB9M9J2RCR7B"
                        },
                        {
                            "orcabusId": "lib.01J5S9CH7TGZMV39Z59WJ8H5GP",
                            "libraryId": "L2400252",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 6.0,
                            "projectOwner": "Whittle",
                            "projectName": "BPOP-retro",
                            "specimen": "spc.01J5S9CH774HEZFEVWWP2XADK1"
                        },
                        {
                            "orcabusId": "lib.01J5S9CH9TGMT2TJGBZX5VXHJY",
                            "libraryId": "L2400253",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "good",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 6.0,
                            "projectOwner": "Whittle",
                            "projectName": "BPOP-retro",
                            "specimen": "spc.01J5S9CH98MQ2B1G2BQFEY0XZH"
                        },
                        {
                            "orcabusId": "lib.01J5S9CHBGAP2XSN4TG8SAMRYY",
                            "libraryId": "L2400254",
                            "phenotype": "tumor",
                            "workflow": "research",
                            "quality": "borderline",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 6.0,
                            "projectOwner": "Whittle",
                            "projectName": "BPOP-retro",
                            "specimen": "spc.01J5S9CHAX3XKJE5XE4VQWYN5H"
                        },
                        {
                            "orcabusId": "lib.01J5S9CHE4ERQ4H209DH397W8A",
                            "libraryId": "L2400255",
                            "phenotype": "tumor",
                            "workflow": "clinical",
                            "quality": "very-poor",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 6.0,
                            "projectOwner": "Tothill",
                            "projectName": "CUP",
                            "specimen": "spc.01J5S9CHDGRNK70B043K887RP2"
                        },
                        {
                            "orcabusId": "lib.01J5S9CHFXPDGYQ8TXHRWQR3PY",
                            "libraryId": "L2400256",
                            "phenotype": "tumor",
                            "workflow": "clinical",
                            "quality": "very-poor",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 6.0,
                            "projectOwner": "Tothill",
                            "projectName": "CUP",
                            "specimen": "spc.01J5S9CHFAPXYKK49FAGVF5CQF"
                        },
                        {
                            "orcabusId": "lib.01J5S9CHHNGFJN73NPRQMSYGN9",
                            "libraryId": "L2400257",
                            "phenotype": "negative-control",
                            "workflow": "control",
                            "quality": "good",
                            "type": "WTS",
                            "assay": "NebRNA",
                            "coverage": 0.1,
                            "projectOwner": "UMCCR",
                            "projectName": "Control",
                            "specimen": "spc.01J5S9CHH24VFM443RD8Q8X4B3"
                        }
                    ],
                    "specimen_obj_list": [
                        {
                            "orcabusId": "spc.01J5S9C0QC2TBZD7XA26D7WGTW",
                            "specimenId": "PRJ240003",
                            "source": "tissue",
                            "subject": "sbj.01J5S9C0PVB4QNVGK4Q1WSYEGV"
                        },
                        {
                            "orcabusId": "spc.01J5S9C4V269YTNA17TTP6NF76",
                            "specimenId": "MDX210402",
                            "source": "plasma-serum",
                            "subject": "sbj.01J5S9C4TE1GCWA1QGNCWHB1Y9"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBFDVZX7ZT3Y6TH28SY4",
                            "specimenId": "PTC_SCMM1pc2",
                            "source": "cfDNA",
                            "subject": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBH4V5B56CEJ5Q1XQKQ9",
                            "specimenId": "PTC_SCMM1pc3",
                            "source": "cfDNA",
                            "subject": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBJTBJB72KJ74VSCHKJF",
                            "specimenId": "PTC_SCMM1pc4",
                            "source": "cfDNA",
                            "subject": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBMKTX5KN1XMPN479R2M",
                            "specimenId": "PTC_SCMM01pc20",
                            "source": "cfDNA",
                            "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBPSPN6S3TQCVJZF0XFE",
                            "specimenId": "PTC_SCMM01pc15",
                            "source": "cfDNA",
                            "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBRM3Y6PPF6E5NWZA7HG",
                            "specimenId": "PTC_SCMM01pc10",
                            "source": "cfDNA",
                            "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBTACFBNJKE8C523B0A7",
                            "specimenId": "PTC_SCMM01pc5",
                            "source": "cfDNA",
                            "subject": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0"
                        },
                        {
                            "orcabusId": "spc.01J5S9CBWCGKQMG5S3ZSWA2ATE",
                            "specimenId": "NTC_v2ctTSO240207",
                            "source": "water",
                            "subject": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6"
                        },
                        {
                            "orcabusId": "spc.01J5S9CDEH0ATXYAK52KW807R4",
                            "specimenId": "PRJ240169",
                            "source": "blood",
                            "subject": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS"
                        },
                        {
                            "orcabusId": "spc.01J5S9CDQ0V9T98EGRPQJAP11S",
                            "specimenId": "PRJ240180",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS"
                        },
                        {
                            "orcabusId": "spc.01J5S9CDRZMMR9S784BYSMVWCT",
                            "specimenId": "PRJ240181",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS"
                        },
                        {
                            "orcabusId": "spc.01J5S9CDTSHGYMMJHE3SXEB2JG",
                            "specimenId": "PRJ240182",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CDG7B0KA8YEDK876VVDP"
                        },
                        {
                            "orcabusId": "spc.01J5S9CDWHAYG4RRG75GYZEK25",
                            "specimenId": "PRJ240183",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CDG7B0KA8YEDK876VVDP"
                        },
                        {
                            "orcabusId": "spc.01J5S9CFWAQTGK4MZB3HM5NVBC",
                            "specimenId": "PRJ240199",
                            "source": "FFPE",
                            "subject": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5"
                        },
                        {
                            "orcabusId": "spc.01J5S9CGBQCSQCS7XR3T89A82F",
                            "specimenId": "PRJ240643",
                            "source": "blood",
                            "subject": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5"
                        },
                        {
                            "orcabusId": "spc.01J5S9CGE05BJCJ20M2KP4QWWB",
                            "specimenId": "PRJ240646",
                            "source": "blood",
                            "subject": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3"
                        },
                        {
                            "orcabusId": "spc.01J5S9CGFQM3BQKADX8TWQ4ZH5",
                            "specimenId": "PRJ240647",
                            "source": "FFPE",
                            "subject": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3"
                        },
                        {
                            "orcabusId": "spc.01J5S9CGHK1G7YXD7C4FCXXS52",
                            "specimenId": "NTC_TSqN240226",
                            "source": "water",
                            "subject": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6"
                        },
                        {
                            "orcabusId": "spc.01J5S9CGKAT4GHZ1VJFHVV15AD",
                            "specimenId": "PTC_TSqN240226",
                            "source": "cell-line",
                            "subject": "sbj.01J5S9BYVWZDS8AW7A94CDQBXK"
                        },
                        {
                            "orcabusId": "spc.01J5S9CH267XEJP5GMZK31MJWS",
                            "specimenId": "PTC_NebRNA240226",
                            "source": "cell-line",
                            "subject": "sbj.01J5S9C1S3XV8PNB78XYJ1EQM1"
                        },
                        {
                            "orcabusId": "spc.01J5S9CH5KXY3VMB9M9J2RCR7B",
                            "specimenId": "PRJ240561",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN"
                        },
                        {
                            "orcabusId": "spc.01J5S9CH774HEZFEVWWP2XADK1",
                            "specimenId": "PRJ240562",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN"
                        },
                        {
                            "orcabusId": "spc.01J5S9CH98MQ2B1G2BQFEY0XZH",
                            "specimenId": "PRJ240566",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CG5GEWYBK0065C49HT23"
                        },
                        {
                            "orcabusId": "spc.01J5S9CHAX3XKJE5XE4VQWYN5H",
                            "specimenId": "PRJ240567",
                            "source": "tissue",
                            "subject": "sbj.01J5S9CG5GEWYBK0065C49HT23"
                        },
                        {
                            "orcabusId": "spc.01J5S9CHDGRNK70B043K887RP2",
                            "specimenId": "PRJ240200",
                            "source": "FFPE",
                            "subject": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5"
                        },
                        {
                            "orcabusId": "spc.01J5S9CHFAPXYKK49FAGVF5CQF",
                            "specimenId": "PRJ240648",
                            "source": "FFPE",
                            "subject": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3"
                        },
                        {
                            "orcabusId": "spc.01J5S9CHH24VFM443RD8Q8X4B3",
                            "specimenId": "NTC_NebRNA240226",
                            "source": "water",
                            "subject": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6"
                        }
                    ],
                    "subject_obj_list": [
                        {
                            "orcabusId": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6",
                            "subjectId": "SBJ00006"
                        },
                        {
                            "orcabusId": "sbj.01J5S9BYVWZDS8AW7A94CDQBXK",
                            "subjectId": "SBJ00005"
                        },
                        {
                            "orcabusId": "sbj.01J5S9C0PVB4QNVGK4Q1WSYEGV",
                            "subjectId": "SBJ04488"
                        },
                        {
                            "orcabusId": "sbj.01J5S9C1S3XV8PNB78XYJ1EQM1",
                            "subjectId": "SBJ00029"
                        },
                        {
                            "orcabusId": "sbj.01J5S9C4TE1GCWA1QGNCWHB1Y9",
                            "subjectId": "SBJ01143"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB",
                            "subjectId": "SBJ04407"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0",
                            "subjectId": "SBJ04648"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS",
                            "subjectId": "SBJ04653"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CDG7B0KA8YEDK876VVDP",
                            "subjectId": "SBJ04654"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5",
                            "subjectId": "SBJ04659"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN",
                            "subjectId": "SBJ04660"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CG5GEWYBK0065C49HT23",
                            "subjectId": "SBJ04661"
                        },
                        {
                            "orcabusId": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3",
                            "subjectId": "SBJ04662"
                        }
                    ]
                },
                None
            ),
            indent=2
        )
    )
    # {
    #   "start_samplesheet_shower_event_data": {
    #     "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5"
    #   },
    #   "complete_samplesheet_shower_event_data": {
    #     "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5"
    #   },
    #   "project_event_data_list": [
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "projectOwner": "Tothill",
    #         "projectName": "CUP",
    #         "libraries": [
    #           {
    #             "orcabusId": "lib.01J5S9CFX5P69S4KZRQGDFKV1N",
    #             "libraryId": "L2400231"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CGCAKQWHD9RBM9VXENY9",
    #             "libraryId": "L2400238"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CGEM1DHRQP72EP09B2TA",
    #             "libraryId": "L2400239"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CGG9N9GH5879SY6A6BJB",
    #             "libraryId": "L2400240"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CHE4ERQ4H209DH397W8A",
    #             "libraryId": "L2400255"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CHFXPDGYQ8TXHRWQR3PY",
    #             "libraryId": "L2400256"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "projectOwner": "VCCC",
    #         "projectName": "PO",
    #         "libraries": [
    #           {
    #             "orcabusId": "lib.01J5S9C4VMJ6PZ8GJ2G189AMXX",
    #             "libraryId": "L2400102"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "projectOwner": "TJohn",
    #         "projectName": "CAVATAK",
    #         "libraries": [
    #           {
    #             "orcabusId": "lib.01J5S9CDF8HHG5PJE3ECJMKMY7",
    #             "libraryId": "L2400191"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S",
    #             "libraryId": "L2400195"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8",
    #             "libraryId": "L2400196"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ",
    #             "libraryId": "L2400197"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CDXCR7Q5K6A8VJRSMM4Q",
    #             "libraryId": "L2400198"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "projectOwner": "UMCCR",
    #         "projectName": "Control",
    #         "libraries": [
    #           {
    #             "orcabusId": "lib.01J5S9CGJ6G09YQ9KFHPSXMMVD",
    #             "libraryId": "L2400241"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CGKWDN7STKZKQM3KH9XR",
    #             "libraryId": "L2400242"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CH2SQ0P1SF7WAT5H4DSE",
    #             "libraryId": "L2400249"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CHHNGFJN73NPRQMSYGN9",
    #             "libraryId": "L2400257"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "projectOwner": "Whittle",
    #         "projectName": "BPOP-retro",
    #         "libraries": [
    #           {
    #             "orcabusId": "lib.01J5S9CH4CYPA4SP05H8KRX4W9",
    #             "libraryId": "L2400250"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CH65E4EE5QJEJ1C60GGG",
    #             "libraryId": "L2400251"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CH7TGZMV39Z59WJ8H5GP",
    #             "libraryId": "L2400252"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CH9TGMT2TJGBZX5VXHJY",
    #             "libraryId": "L2400253"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CHBGAP2XSN4TG8SAMRYY",
    #             "libraryId": "L2400254"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "projectOwner": "UMCCR",
    #         "projectName": "Testing",
    #         "libraries": [
    #           {
    #             "orcabusId": "lib.01J5S9CBG0NF8QBNVKM6ESCD60",
    #             "libraryId": "L2400159"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CBHP6NSB42RVFAP9PGJP",
    #             "libraryId": "L2400160"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CBKCATYSFY40BRX6WJWX",
    #             "libraryId": "L2400161"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CBN6EAXW4AXG7TQ1H6NC",
    #             "libraryId": "L2400162"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CBQFX8V1QRW7KAV3MD1W",
    #             "libraryId": "L2400163"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CBS64DNTHK6CE850CCNZ",
    #             "libraryId": "L2400164"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CBTZRYQNTGAHPC2T601D",
    #             "libraryId": "L2400165"
    #           },
    #           {
    #             "orcabusId": "lib.01J5S9CBX10204CK7EKGTH9TMB",
    #             "libraryId": "L2400166"
    #           }
    #         ]
    #       }
    #     }
    #   ],
    #   "subject_event_data_list": [
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6",
    #           "subjectId": "SBJ00006"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9BYVWZDS8AW7A94CDQBXK",
    #           "subjectId": "SBJ00005"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9C0PVB4QNVGK4Q1WSYEGV",
    #           "subjectId": "SBJ04488"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9C1S3XV8PNB78XYJ1EQM1",
    #           "subjectId": "SBJ00029"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9C4TE1GCWA1QGNCWHB1Y9",
    #           "subjectId": "SBJ01143"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB",
    #           "subjectId": "SBJ04407"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0",
    #           "subjectId": "SBJ04648"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS",
    #           "subjectId": "SBJ04653"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CDG7B0KA8YEDK876VVDP",
    #           "subjectId": "SBJ04654"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5",
    #           "subjectId": "SBJ04659"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN",
    #           "subjectId": "SBJ04660"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CG5GEWYBK0065C49HT23",
    #           "subjectId": "SBJ04661"
    #         }
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "subject": {
    #           "orcabusId": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3",
    #           "subjectId": "SBJ04662"
    #         }
    #       }
    #     }
    #   ],
    #   "library_event_data_list": [
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9C4VMJ6PZ8GJ2G189AMXX",
    #           "libraryId": "L2400102",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "borderline",
    #           "type": "WGS",
    #           "assay": "ctTSO",
    #           "coverage": 50.0,
    #           "projectOwner": "VCCC",
    #           "projectName": "PO",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9C4V269YTNA17TTP6NF76",
    #             "specimenId": "MDX210402"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9C4TE1GCWA1QGNCWHB1Y9",
    #             "subjectId": "SBJ01143"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400102",
    #             "index": "GAATTCGT",
    #             "index2": "TTATGAGT",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GAATTCGT.TTATGAGT.1.240424_A01052_0193_BH7JMMDRX5.L2400102"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBG0NF8QBNVKM6ESCD60",
    #           "libraryId": "L2400159",
    #           "phenotype": "tumor",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 38.6,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBFDVZX7ZT3Y6TH28SY4",
    #             "specimenId": "PTC_SCMM1pc2"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB",
    #             "subjectId": "SBJ04407"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400159",
    #             "index": "GAGAATGGTT",
    #             "index2": "TTGCTGCCGA",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GAGAATGGTT.TTGCTGCCGA.1.240424_A01052_0193_BH7JMMDRX5.L2400159"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBHP6NSB42RVFAP9PGJP",
    #           "libraryId": "L2400160",
    #           "phenotype": "tumor",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 38.6,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBH4V5B56CEJ5Q1XQKQ9",
    #             "specimenId": "PTC_SCMM1pc3"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB",
    #             "subjectId": "SBJ04407"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400160",
    #             "index": "AGAGGCAACC",
    #             "index2": "CCATCATTAG",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "AGAGGCAACC.CCATCATTAG.1.240424_A01052_0193_BH7JMMDRX5.L2400160"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBKCATYSFY40BRX6WJWX",
    #           "libraryId": "L2400161",
    #           "phenotype": "tumor",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 38.6,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBJTBJB72KJ74VSCHKJF",
    #             "specimenId": "PTC_SCMM1pc4"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CBEQ3DM8XDV2G2ZQJDXB",
    #             "subjectId": "SBJ04407"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400161",
    #             "index": "CCATCATTAG",
    #             "index2": "AGAGGCAACC",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "CCATCATTAG.AGAGGCAACC.1.240424_A01052_0193_BH7JMMDRX5.L2400161"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBN6EAXW4AXG7TQ1H6NC",
    #           "libraryId": "L2400162",
    #           "phenotype": "tumor",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 38.6,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBMKTX5KN1XMPN479R2M",
    #             "specimenId": "PTC_SCMM01pc20"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0",
    #             "subjectId": "SBJ04648"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400162",
    #             "index": "GATAGGCCGA",
    #             "index2": "GCCATGTGCG",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GATAGGCCGA.GCCATGTGCG.1.240424_A01052_0193_BH7JMMDRX5.L2400162"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBQFX8V1QRW7KAV3MD1W",
    #           "libraryId": "L2400163",
    #           "phenotype": "tumor",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 38.6,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBPSPN6S3TQCVJZF0XFE",
    #             "specimenId": "PTC_SCMM01pc15"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0",
    #             "subjectId": "SBJ04648"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400163",
    #             "index": "ATGGTTGACT",
    #             "index2": "AGGACAGGCC",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "ATGGTTGACT.AGGACAGGCC.1.240424_A01052_0193_BH7JMMDRX5.L2400163"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBS64DNTHK6CE850CCNZ",
    #           "libraryId": "L2400164",
    #           "phenotype": "tumor",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 38.6,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBRM3Y6PPF6E5NWZA7HG",
    #             "specimenId": "PTC_SCMM01pc10"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0",
    #             "subjectId": "SBJ04648"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400164",
    #             "index": "TATTGCGCTC",
    #             "index2": "CCTAACACAG",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "TATTGCGCTC.CCTAACACAG.1.240424_A01052_0193_BH7JMMDRX5.L2400164"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBTZRYQNTGAHPC2T601D",
    #           "libraryId": "L2400165",
    #           "phenotype": "tumor",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 38.6,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBTACFBNJKE8C523B0A7",
    #             "specimenId": "PTC_SCMM01pc5"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CBM3AT89QTXD7PT0BKA0",
    #             "subjectId": "SBJ04648"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400165",
    #             "index": "ACGCCTTGTT",
    #             "index2": "ACGTTCCTTA",
    #             "lane": 4,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "ACGCCTTGTT.ACGTTCCTTA.4.240424_A01052_0193_BH7JMMDRX5.L2400165"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CBX10204CK7EKGTH9TMB",
    #           "libraryId": "L2400166",
    #           "phenotype": "negative-control",
    #           "workflow": "manual",
    #           "quality": "good",
    #           "type": "ctDNA",
    #           "assay": "ctTSOv2",
    #           "coverage": 0.1,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Testing",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CBWCGKQMG5S3ZSWA2ATE",
    #             "specimenId": "NTC_v2ctTSO240207"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6",
    #             "subjectId": "SBJ00006"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400166",
    #             "index": "TTCTACATAC",
    #             "index2": "TTACAGTTAG",
    #             "lane": 1,
    #             "overrideCycles": "U7N1Y143;I10;I10;U7N1Y143"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "TTCTACATAC.TTACAGTTAG.1.240424_A01052_0193_BH7JMMDRX5.L2400166"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CDF8HHG5PJE3ECJMKMY7",
    #           "libraryId": "L2400191",
    #           "phenotype": "normal",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 40.0,
    #           "projectOwner": "TJohn",
    #           "projectName": "CAVATAK",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CDEH0ATXYAK52KW807R4",
    #             "specimenId": "PRJ240169"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS",
    #             "subjectId": "SBJ04653"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400191",
    #             "index": "GCACGGAC",
    #             "index2": "TGCGAGAC",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GCACGGAC.TGCGAGAC.4.240424_A01052_0193_BH7JMMDRX5.L2400191"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CDQSSAG1WYCRWMD82Z1S",
    #           "libraryId": "L2400195",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 80.0,
    #           "projectOwner": "TJohn",
    #           "projectName": "CAVATAK",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CDQ0V9T98EGRPQJAP11S",
    #             "specimenId": "PRJ240180"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS",
    #             "subjectId": "SBJ04653"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400195",
    #             "index": "ATGAGGCC",
    #             "index2": "CAATTAAC",
    #             "lane": 2,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400195",
    #             "index": "ATGAGGCC",
    #             "index2": "CAATTAAC",
    #             "lane": 3,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "ATGAGGCC.CAATTAAC.2.240424_A01052_0193_BH7JMMDRX5.L2400195"
    #           },
    #           {
    #             "fastqListRowRgid": "ATGAGGCC.CAATTAAC.3.240424_A01052_0193_BH7JMMDRX5.L2400195"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CDSJ2BGEYM8FTXGKVGV8",
    #           "libraryId": "L2400196",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 80.0,
    #           "projectOwner": "TJohn",
    #           "projectName": "CAVATAK",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CDRZMMR9S784BYSMVWCT",
    #             "specimenId": "PRJ240181"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CDDP20JX8V63ZKMPBJQS",
    #             "subjectId": "SBJ04653"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400196",
    #             "index": "ACTAAGAT",
    #             "index2": "CCGCGGTT",
    #             "lane": 2,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400196",
    #             "index": "ACTAAGAT",
    #             "index2": "CCGCGGTT",
    #             "lane": 3,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "ACTAAGAT.CCGCGGTT.2.240424_A01052_0193_BH7JMMDRX5.L2400196"
    #           },
    #           {
    #             "fastqListRowRgid": "ACTAAGAT.CCGCGGTT.3.240424_A01052_0193_BH7JMMDRX5.L2400196"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CDVEHDZHZR3BZTQ7WNJQ",
    #           "libraryId": "L2400197",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 80.0,
    #           "projectOwner": "TJohn",
    #           "projectName": "CAVATAK",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CDTSHGYMMJHE3SXEB2JG",
    #             "specimenId": "PRJ240182"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CDG7B0KA8YEDK876VVDP",
    #             "subjectId": "SBJ04654"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400197",
    #             "index": "GTCGGAGC",
    #             "index2": "TTATAACC",
    #             "lane": 2,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400197",
    #             "index": "GTCGGAGC",
    #             "index2": "TTATAACC",
    #             "lane": 3,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400197",
    #             "index": "GTCGGAGC",
    #             "index2": "TTATAACC",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GTCGGAGC.TTATAACC.2.240424_A01052_0193_BH7JMMDRX5.L2400197"
    #           },
    #           {
    #             "fastqListRowRgid": "GTCGGAGC.TTATAACC.3.240424_A01052_0193_BH7JMMDRX5.L2400197"
    #           },
    #           {
    #             "fastqListRowRgid": "GTCGGAGC.TTATAACC.4.240424_A01052_0193_BH7JMMDRX5.L2400197"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CDXCR7Q5K6A8VJRSMM4Q",
    #           "libraryId": "L2400198",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 80.0,
    #           "projectOwner": "TJohn",
    #           "projectName": "CAVATAK",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CDWHAYG4RRG75GYZEK25",
    #             "specimenId": "PRJ240183"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CDG7B0KA8YEDK876VVDP",
    #             "subjectId": "SBJ04654"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400198",
    #             "index": "CTTGGTAT",
    #             "index2": "GGACTTGG",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "CTTGGTAT.GGACTTGG.4.240424_A01052_0193_BH7JMMDRX5.L2400198"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CFX5P69S4KZRQGDFKV1N",
    #           "libraryId": "L2400231",
    #           "phenotype": "tumor",
    #           "workflow": "clinical",
    #           "quality": "poor",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 100.0,
    #           "projectOwner": "Tothill",
    #           "projectName": "CUP",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CFWAQTGK4MZB3HM5NVBC",
    #             "specimenId": "PRJ240199"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5",
    #             "subjectId": "SBJ04659"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400231",
    #             "index": "TCGTAGTG",
    #             "index2": "CCAAGTCT",
    #             "lane": 2,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400231",
    #             "index": "TCGTAGTG",
    #             "index2": "CCAAGTCT",
    #             "lane": 3,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "TCGTAGTG.CCAAGTCT.2.240424_A01052_0193_BH7JMMDRX5.L2400231"
    #           },
    #           {
    #             "fastqListRowRgid": "TCGTAGTG.CCAAGTCT.3.240424_A01052_0193_BH7JMMDRX5.L2400231"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CGCAKQWHD9RBM9VXENY9",
    #           "libraryId": "L2400238",
    #           "phenotype": "normal",
    #           "workflow": "clinical",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 40.0,
    #           "projectOwner": "Tothill",
    #           "projectName": "CUP",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CGBQCSQCS7XR3T89A82F",
    #             "specimenId": "PRJ240643"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5",
    #             "subjectId": "SBJ04659"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400238",
    #             "index": "GGAGCGTC",
    #             "index2": "GCACGGAC",
    #             "lane": 2,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400238",
    #             "index": "GGAGCGTC",
    #             "index2": "GCACGGAC",
    #             "lane": 3,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GGAGCGTC.GCACGGAC.2.240424_A01052_0193_BH7JMMDRX5.L2400238"
    #           },
    #           {
    #             "fastqListRowRgid": "GGAGCGTC.GCACGGAC.3.240424_A01052_0193_BH7JMMDRX5.L2400238"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CGEM1DHRQP72EP09B2TA",
    #           "libraryId": "L2400239",
    #           "phenotype": "normal",
    #           "workflow": "clinical",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 40.0,
    #           "projectOwner": "Tothill",
    #           "projectName": "CUP",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CGE05BJCJ20M2KP4QWWB",
    #             "specimenId": "PRJ240646"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3",
    #             "subjectId": "SBJ04662"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400239",
    #             "index": "ATGGCATG",
    #             "index2": "GGTACCTT",
    #             "lane": 2,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400239",
    #             "index": "ATGGCATG",
    #             "index2": "GGTACCTT",
    #             "lane": 3,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "ATGGCATG.GGTACCTT.2.240424_A01052_0193_BH7JMMDRX5.L2400239"
    #           },
    #           {
    #             "fastqListRowRgid": "ATGGCATG.GGTACCTT.3.240424_A01052_0193_BH7JMMDRX5.L2400239"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CGG9N9GH5879SY6A6BJB",
    #           "libraryId": "L2400240",
    #           "phenotype": "tumor",
    #           "workflow": "clinical",
    #           "quality": "poor",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 100.0,
    #           "projectOwner": "Tothill",
    #           "projectName": "CUP",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CGFQM3BQKADX8TWQ4ZH5",
    #             "specimenId": "PRJ240647"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3",
    #             "subjectId": "SBJ04662"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400240",
    #             "index": "GCAATGCA",
    #             "index2": "AACGTTCC",
    #             "lane": 2,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           },
    #           {
    #             "sampleId": "L2400240",
    #             "index": "GCAATGCA",
    #             "index2": "AACGTTCC",
    #             "lane": 3,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GCAATGCA.AACGTTCC.2.240424_A01052_0193_BH7JMMDRX5.L2400240"
    #           },
    #           {
    #             "fastqListRowRgid": "GCAATGCA.AACGTTCC.3.240424_A01052_0193_BH7JMMDRX5.L2400240"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CGJ6G09YQ9KFHPSXMMVD",
    #           "libraryId": "L2400241",
    #           "phenotype": "negative-control",
    #           "workflow": "control",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 0.1,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Control",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CGHK1G7YXD7C4FCXXS52",
    #             "specimenId": "NTC_TSqN240226"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6",
    #             "subjectId": "SBJ00006"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400241",
    #             "index": "GTTCCAAT",
    #             "index2": "GCAGAATT",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GTTCCAAT.GCAGAATT.4.240424_A01052_0193_BH7JMMDRX5.L2400241"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CGKWDN7STKZKQM3KH9XR",
    #           "libraryId": "L2400242",
    #           "phenotype": "normal",
    #           "workflow": "control",
    #           "quality": "good",
    #           "type": "WGS",
    #           "assay": "TsqNano",
    #           "coverage": 15.0,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Control",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CGKAT4GHZ1VJFHVV15AD",
    #             "specimenId": "PTC_TSqN240226"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9BYVWZDS8AW7A94CDQBXK",
    #             "subjectId": "SBJ00005"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400242",
    #             "index": "ACCTTGGC",
    #             "index2": "ATGAGGCC",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "ACCTTGGC.ATGAGGCC.4.240424_A01052_0193_BH7JMMDRX5.L2400242"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CH2SQ0P1SF7WAT5H4DSE",
    #           "libraryId": "L2400249",
    #           "phenotype": "tumor",
    #           "workflow": "control",
    #           "quality": "good",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 1.0,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Control",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CH267XEJP5GMZK31MJWS",
    #             "specimenId": "PTC_NebRNA240226"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9C1S3XV8PNB78XYJ1EQM1",
    #             "subjectId": "SBJ00029"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400249",
    #             "index": "AGTTTCGA",
    #             "index2": "CCTACGAT",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "AGTTTCGA.CCTACGAT.4.240424_A01052_0193_BH7JMMDRX5.L2400249"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CH4CYPA4SP05H8KRX4W9",
    #           "libraryId": "L2400250",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 6.0,
    #           "projectOwner": "Whittle",
    #           "projectName": "BPOP-retro",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9C0QC2TBZD7XA26D7WGTW",
    #             "specimenId": "PRJ240003"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9C0PVB4QNVGK4Q1WSYEGV",
    #             "subjectId": "SBJ04488"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400250",
    #             "index": "GAACCTCT",
    #             "index2": "GTCTGCGC",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GAACCTCT.GTCTGCGC.4.240424_A01052_0193_BH7JMMDRX5.L2400250"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CH65E4EE5QJEJ1C60GGG",
    #           "libraryId": "L2400251",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 6.0,
    #           "projectOwner": "Whittle",
    #           "projectName": "BPOP-retro",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CH5KXY3VMB9M9J2RCR7B",
    #             "specimenId": "PRJ240561"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN",
    #             "subjectId": "SBJ04660"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400251",
    #             "index": "GCCCAGTG",
    #             "index2": "CCGCAATT",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GCCCAGTG.CCGCAATT.4.240424_A01052_0193_BH7JMMDRX5.L2400251"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CH7TGZMV39Z59WJ8H5GP",
    #           "libraryId": "L2400252",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 6.0,
    #           "projectOwner": "Whittle",
    #           "projectName": "BPOP-retro",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CH774HEZFEVWWP2XADK1",
    #             "specimenId": "PRJ240562"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CFY1BV2Z0SGKYNF1VHQN",
    #             "subjectId": "SBJ04660"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400252",
    #             "index": "TGACAGCT",
    #             "index2": "CCCGTAGG",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "TGACAGCT.CCCGTAGG.4.240424_A01052_0193_BH7JMMDRX5.L2400252"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CH9TGMT2TJGBZX5VXHJY",
    #           "libraryId": "L2400253",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "good",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 6.0,
    #           "projectOwner": "Whittle",
    #           "projectName": "BPOP-retro",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CH98MQ2B1G2BQFEY0XZH",
    #             "specimenId": "PRJ240566"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CG5GEWYBK0065C49HT23",
    #             "subjectId": "SBJ04661"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400253",
    #             "index": "CATCACCC",
    #             "index2": "ATATAGCA",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "CATCACCC.ATATAGCA.4.240424_A01052_0193_BH7JMMDRX5.L2400253"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CHBGAP2XSN4TG8SAMRYY",
    #           "libraryId": "L2400254",
    #           "phenotype": "tumor",
    #           "workflow": "research",
    #           "quality": "borderline",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 6.0,
    #           "projectOwner": "Whittle",
    #           "projectName": "BPOP-retro",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CHAX3XKJE5XE4VQWYN5H",
    #             "specimenId": "PRJ240567"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CG5GEWYBK0065C49HT23",
    #             "subjectId": "SBJ04661"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400254",
    #             "index": "CTGGAGTA",
    #             "index2": "GTTCGGTT",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "CTGGAGTA.GTTCGGTT.4.240424_A01052_0193_BH7JMMDRX5.L2400254"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CHE4ERQ4H209DH397W8A",
    #           "libraryId": "L2400255",
    #           "phenotype": "tumor",
    #           "workflow": "clinical",
    #           "quality": "very-poor",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 6.0,
    #           "projectOwner": "Tothill",
    #           "projectName": "CUP",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CHDGRNK70B043K887RP2",
    #             "specimenId": "PRJ240200"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CFVJ9GVEHZK6CD9WAAV5",
    #             "subjectId": "SBJ04659"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400255",
    #             "index": "GATCCGGG",
    #             "index2": "AAGCAGGT",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GATCCGGG.AAGCAGGT.4.240424_A01052_0193_BH7JMMDRX5.L2400255"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CHFXPDGYQ8TXHRWQR3PY",
    #           "libraryId": "L2400256",
    #           "phenotype": "tumor",
    #           "workflow": "clinical",
    #           "quality": "very-poor",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 6.0,
    #           "projectOwner": "Tothill",
    #           "projectName": "CUP",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CHFAPXYKK49FAGVF5CQF",
    #             "specimenId": "PRJ240648"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9CGDGTF5VZJSSE4ADBNJ3",
    #             "subjectId": "SBJ04662"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400256",
    #             "index": "AACACCTG",
    #             "index2": "CGCATGGG",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "AACACCTG.CGCATGGG.4.240424_A01052_0193_BH7JMMDRX5.L2400256"
    #           }
    #         ]
    #       }
    #     },
    #     {
    #       "event_data": {
    #         "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
    #         "library": {
    #           "orcabusId": "lib.01J5S9CHHNGFJN73NPRQMSYGN9",
    #           "libraryId": "L2400257",
    #           "phenotype": "negative-control",
    #           "workflow": "control",
    #           "quality": "good",
    #           "type": "WTS",
    #           "assay": "NebRNA",
    #           "coverage": 0.1,
    #           "projectOwner": "UMCCR",
    #           "projectName": "Control",
    #           "specimen": {
    #             "orcabusId": "spc.01J5S9CHH24VFM443RD8Q8X4B3",
    #             "specimenId": "NTC_NebRNA240226"
    #           },
    #           "subject": {
    #             "orcabusId": "sbj.01J5S9BYKC1RH7DY68GF1JNSR6",
    #             "subjectId": "SBJ00006"
    #           }
    #         },
    #         "bclconvertDataRows": [
    #           {
    #             "sampleId": "L2400257",
    #             "index": "GTGACGTT",
    #             "index2": "TCCCAGAT",
    #             "lane": 4,
    #             "overrideCycles": "Y151;I8N2;I8N2;Y151"
    #           }
    #         ],
    #         "fastqListRows": [
    #           {
    #             "fastqListRowRgid": "GTGACGTT.TCCCAGAT.4.240424_A01052_0193_BH7JMMDRX5.L2400257"
    #           }
    #         ]
    #       }
    #     }
    #   ]
    # }
