#!/usr/bin/env python3

"""
LAMBDA_ARN_SFN_PLACEHOLDER: __handle_workflow_inputs_lambda_function_arn__

This script is used to handle the inputs for the aws step function

We take in the following inputs

* instrumentRunIdList
* libraryIdList
* subjectIdList
* individualIdList
* projectIdList
* dataTypeList
* defrostArchivedFastqs
* secondaryAnalysisWorkflowList
* portalRunIdList
* portalRunIdExclusionList

And export the following outputs / variables to be used in the aws step function

* libraryOrcabusIdList (list of library orcabus ids, these are first converted to library objects in the first map state of the step function and uploaded to s3)
* instrumentRunIdList (list of instrument run ids, used for filtering fastq objects if the dataTypeList includes fastqs)
* portalRunIdList (list of portal run ids, used for filtering secondary analysis objects if the dataTypeList includes secondaryAnalysis)
* portalRunIdExclusionList (list of portal run ids to exclude, used for filtering secondary analysis objects if the dataTypeList includes secondaryAnalysis)
* dataTypeList (list of data types, one of 'fastqs', 'secondaryAnalysis')
* secondaryAnalysisWorkflowList (list of secondary analysis workflow ids, used for filtering secondary analysis objects if the dataTypeList includes secondaryAnalysis)
* defrostArchivedFastqs, boolean, if true, we will defrost archived fastqs, only used if dataTypeList includes fastqs (and there are fastqs to defrost)

We have a few different use-cases to consider:

FASTQ Use Cases:

1. One (or more) libraries - where we need to transfer fastq data
2. Full Instrument Run of Fastqs - where we need to transfer fastq data for all libraries in the instrument run
3. Archived Libraries - where we need to defrost archived fastqs
4. Share on another metadata id, such as subject, individual or project level, convert to library list, and share the data

Secondary Analysis Use Cases:
1. Given a metadata id, find all secondary analysis objects and share them
2. Given a metadata id AND a list of secondaryAnalysisWorkflowLists, find all secondary analysis objects and share them
3. Given a list of metadata ids, portal run ids and secondaryAnalysisWorkflowLists, find all secondary analysis objects and share them but share only files in the portal run ids.

"""
from typing import Optional, List
from enum import Enum
from functools import reduce
from operator import concat

from data_sharing_tools.utils.models import SecondaryAnalysisDataTypeEnum, DataTypeEnum
# Layer imports
from metadata_tools import (
    coerce_subject_id_or_orcabus_id_to_subject_orcabus_id, list_libraries_in_subject,
    list_libraries_in_individual, coerce_individual_id_or_orcabus_id_to_individual_orcabus_id,
    get_library_from_library_id, list_libraries_in_project, coerce_project_id_or_orcabus_id_to_project_orcabus_id
)
from fastq_tools import (
    get_fastqs_in_library_list
)

# Set logging
import logging
logger = logging.getLogger()
logger.setLevel("INFO")


def confirm_input_is_list_str_type(input_variable: Optional[List[str]], input_variable_name: str):
    """
    Confirm that the input variable is a list of strings
    :param input_variable:
    :param input_variable_name:
    :return:
    """
    if input_variable is None:
        return

    assert isinstance(input_variable, list), f"{input_variable_name} must be a list of strings"

    if len(input_variable) > 0:
        assert all(isinstance(x, str) for x in input_variable), f"{input_variable_name} must be a list of strings"


class ShareTypeEnum(Enum):
    PUSH = "push"
    PULL = "pull"


def handler(event, context):
    """
    Handle the inputs for the aws step function
    :param event:
    :param context:
    :return:
    """

    # Get the inputs from the event
    instrument_run_id_list: Optional[List[str]] = event.get("instrumentRunIdList")
    library_id_list: Optional[List[str]] = event.get("libraryIdList")
    subject_id_list: Optional[List[str]] = event.get("subjectIdList")
    individual_id_list: Optional[List[str]] = event.get("individualIdList")
    project_id_list: Optional[List[str]] = event.get("projectIdList")
    data_type_list: Optional[List[str]] = event.get("dataTypeList")
    defrost_archived_fastqs: Optional[bool] = event.get("defrostArchivedFastqs")
    secondary_analysis_type_list: Optional[List[str]] = event.get("secondaryAnalysisTypeList")
    portal_run_id_list: Optional[List[str]] = event.get("portalRunIdList")
    portal_run_id_exclusion_list: Optional[List[str]] = event.get("portalRunIdExclusionList")

    # Confirm that if instrument run id list is provided, that
    # the variables data type is a list of strings
    for input_variable, input_variable_name in [
        (instrument_run_id_list, "instrumentRunIdList"),
        (library_id_list, "libraryIdList"),
        (subject_id_list, "subjectIdList"),
        (individual_id_list, "individualIdList"),
        (project_id_list, "projectIdList"),
        (data_type_list, "dataTypeList"),
        (secondary_analysis_type_list, "secondaryAnalysisWorkflowList"),
        (portal_run_id_list, "portalRunIdList"),
        (portal_run_id_exclusion_list, "portalRunIdExclusionList"),
    ]:
        confirm_input_is_list_str_type(input_variable, input_variable_name)

    # Confirm defrost_archived_fastqs is a boolean value
    if defrost_archived_fastqs is None:
        # Set default to false
        defrost_archived_fastqs = False

    # Confirm only one of library_id_list, subject_id_list, individual_id_list, project_id_list is provided
    if len(list(filter(lambda meta_iter_: meta_iter_ is not None, [library_id_list, subject_id_list, individual_id_list, project_id_list]))) > 1:
        logger.error("Only one of libraryIdList, subjectIdList, individualIdList, projectIdList can be provided")
        raise ValueError("Only one of libraryIdList, subjectIdList, individualIdList, projectIdList can be provided")

    # Metadata, convert to library orcabus ids
    # This is a good litmus test to ensure that all library ids are in the metadata portal
    library_orcabus_id_list = []  # Initialise, since we may not use it if we are using only going off secondary analyses
    if library_id_list is not None:
        library_orcabus_id_list = list(map(
            lambda library_id_iter_: get_library_from_library_id(library_id_iter_)["orcabusId"],
            list(set(library_id_list))
        ))
    if subject_id_list is not None:
        library_orcabus_id_list = list(set(list(map(
            lambda library_obj_iter_: library_obj_iter_["orcabusId"],
            list(reduce(
                concat,
                list(map(
                    lambda subject_iter_: list_libraries_in_subject(coerce_subject_id_or_orcabus_id_to_subject_orcabus_id(subject_iter_)),
                    subject_id_list
                ))
            )),
        ))))
    if individual_id_list is not None:
        library_orcabus_id_list = list(set(list(map(
            lambda library_obj_iter_: library_obj_iter_["orcabusId"],
            list(reduce(
                concat,
                list(map(
                    lambda individual_iter_: list_libraries_in_individual(coerce_individual_id_or_orcabus_id_to_individual_orcabus_id(individual_iter_)),
                    individual_id_list
                ))
            )),
        ))))
    if project_id_list is not None:
        library_orcabus_id_list = list(set(list(map(
            lambda library_obj_iter_: library_obj_iter_["orcabusId"],
            list(reduce(
                concat,
                list(map(
                    lambda project_iter_: list_libraries_in_project(coerce_project_id_or_orcabus_id_to_project_orcabus_id(project_iter_)),
                    project_id_list
                ))
            )),
        ))))
    # Coerce data types
    if data_type_list is None:
        logger.error("Data type list must be provided")
        raise ValueError("Data type list must be provided")
    data_type_list: List[DataTypeEnum] = list(set(list(map(
        lambda data_type_iter_: DataTypeEnum[data_type_iter_],
        data_type_list
    ))))

    # Secondary analysis data type list
    if secondary_analysis_type_list is not None:
        secondary_analysis_type_list: List[SecondaryAnalysisDataTypeEnum] = list(set(list(map(
            lambda secondary_analysis_workflow_iter_: SecondaryAnalysisDataTypeEnum(secondary_analysis_workflow_iter_.lower()),
            secondary_analysis_type_list
        ))))
    else:
        secondary_analysis_type_list = []

    # Filter libraries by the instrument run id list
    # This is respected by both fastq and secondary analysis data types
    if instrument_run_id_list is not None:
        library_orcabus_id_list = sorted(list(set(list(map(
            lambda fastq_iter_: fastq_iter_['library']["orcabusId"],
            list(filter(
                lambda fastq_iter: fastq_iter["instrumentRunId"] in instrument_run_id_list,
                get_fastqs_in_library_list(library_orcabus_id_list)
            ))
        )))))

    # Export the variables
    return {
        "libraryOrcabusIdList": library_orcabus_id_list,
        "instrumentRunIdList": instrument_run_id_list,
        "portalRunIdList": portal_run_id_list,
        "portalRunIdExclusionList": portal_run_id_exclusion_list,
        "defrostArchivedFastqs": defrost_archived_fastqs,
        "dataTypeList": list(map(lambda data_type_iter_: data_type_iter_.value, data_type_list)),
        "secondaryAnalysisTypeList": list(map(
            lambda secondary_analysis_type_iter_: secondary_analysis_type_iter_.value,
            secondary_analysis_type_list
        ))
    }

# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "libraryIdList": [
#                         "L2401544"
#                     ],
#                     "dataTypeList": [
#                         "FASTQ"
#                     ]
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "libraryOrcabusIdList": [
#     #         "lib.01JBMW08H093THDFYS4467C2RW"
#     #     ],
#     #     "instrumentRunIdList": null,
#     #     "portalRunIdList": null,
#     #     "portalRunIdExclusionList": null,
#     #     "defrostArchivedFastqs": false,
#     #     "dataTypeList": [
#     #         "fastq"
#     #     ],
#     #     "secondaryAnalysisWorkflowList": []
#     # }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "projectIdList": [
#                         "BPOP"
#                     ],
#                     "instrumentRunIdList": [
#                         "241024_A00130_0336_BHW7MVDSXC"
#                     ],
#                     "dataTypeList": [
#                         "FASTQ",
#                         "SECONDARY_ANALYSIS"
#                     ],
#                     "secondaryAnalysisTypeList": [
#                         "tumor-normal",
#                         "wts",
#                         "cttsov2",
#                         "umccrise",
#                         "rnasum"
#                     ]
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )

    # {
    #     "libraryOrcabusIdList": [
    #         "lib.01JBMW08H093THDFYS4467C2RW"
    #     ],
    #     "instrumentRunIdList": null,
    #     "portalRunIdList": [
    #         "2024111463c05a04"
    #     ],
    #     "portalRunIdExclusionList": null,
    #     "defrostArchivedFastqs": false,
    #     "dataTypeList": [
    #         "fastq",
    #         "secondaryAnalysis"
    #     ],
    #     "secondaryAnalysisWorkflowList": []
    # }
