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
* shareType
* shareDestination
* dryrun

And export the following outputs / variables to be used in the aws step function

* libraryOrcabusIdList (list of library orcabus ids, these are first converted to library objects in the first map state of the step function and uploaded to s3)
* instrumentRunIdList (list of instrument run ids, used for filtering fastq objects if the dataTypeList includes fastqs)
* portalRunIdList (list of portal run ids, used for filtering secondary analysis objects if the dataTypeList includes secondaryAnalysis)
* portalRunIdExclusionList (list of portal run ids to exclude, used for filtering secondary analysis objects if the dataTypeList includes secondaryAnalysis)
* dataTypeList (list of data types, one of 'fastqs', 'secondaryAnalysis')
* secondaryAnalysisWorkflowList (list of secondary analysis workflow ids, used for filtering secondary analysis objects if the dataTypeList includes secondaryAnalysis)
* shareType, one of 'push' or 'pull'
* shareDestination, the destination for the shared files, only used if shareType is 'push'
* defrostArchivedFastqs, boolean, if true, we will defrost archived fastqs, only used if dataTypeList includes fastqs (and there are fastqs to defrost)
* dryRun

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


# Layer imports
from metadata_tools import (
    coerce_subject_id_or_orcabus_id_to_subject_orcabus_id, list_libraries_in_subject,
    list_libraries_in_individual, coerce_individual_id_or_orcabus_id_to_individual_orcabus_id,
    get_library_from_library_id, list_libraries_in_project, coerce_project_id_or_orcabus_id_to_project_orcabus_id
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
    if input_variable is not None:
        assert isinstance(input_variable, list), f"{input_variable_name} must be a list of strings"

    if len(input_variable) > 0:
        assert all(isinstance(x, str) for x in input_variable), f"{input_variable_name} must be a list of strings"


class ShareTypeEnum(Enum):
    PUSH = "push"
    PULL = "pull"


class DataTypeEnum(Enum):
    FASTQ = "fastq"
    SECONDARY_ANALYSIS = "secondaryAnalysis"


class SecondaryAnalysisDataTypeEnum(Enum):
    # CURRENT
    TUMOR_NORMAL = "tumor-normal"
    WTS = "wts"
    CTTSOV2 = "cttsov2"

    # FUTURE
    DRAGEN_WGTS_DNA = 'dragen-wgts-dna'
    DRAGEN_WGTS_RNA = 'dragen-wgts-rna'
    DRAGEN_TSO500_CTDNA = 'dragen-tso500-ctdna'

    # ONCOANALYSER
    ONCOANALYSER_WGTS_DNA = 'oncoanalyser-wgts-dna'
    ONCOANALYSER_WGTS_RNA = 'oncoanalyser-wgts-rna'
    ONCOANALYSER_WGTS_DNA_RNA = 'oncoanalyser-wgts-dna-rna'

    SASH = 'sash'
    UMCCRISE = 'umccrise'
    RNASUM = 'rnasum'


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
    secondary_analysis_workflow_list: Optional[List[str]] = event.get("secondaryAnalysisWorkflowList")
    portal_run_id_list: Optional[List[str]] = event.get("portalRunIdList")
    portal_run_id_exclusion_list: Optional[List[str]] = event.get("portalRunIdExclusionList")
    share_type: ShareTypeEnum = event.get("shareType")
    share_destination: Optional[str] = event.get("shareDestination")
    dryrun: Optional[bool] = event.get("dryrun")

    # Confirm that if instrument run id list is provided, that
    # the variables data type is a list of strings
    for input_variable, input_variable_name in [
        (instrument_run_id_list, "instrumentRunIdList"),
        (library_id_list, "libraryIdList"),
        (subject_id_list, "subjectIdList"),
        (individual_id_list, "individualIdList"),
        (project_id_list, "projectIdList"),
        (data_type_list, "dataTypeList"),
        (secondary_analysis_workflow_list, "secondaryAnalysisWorkflowList"),
        (portal_run_id_list, "portalRunIdList"),
        (portal_run_id_exclusion_list, "portalRunIdExclusionList"),
    ]:
        confirm_input_is_list_str_type(input_variable, input_variable_name)

    # Confirm defrost_archived_fastqs is a boolean value
    if defrost_archived_fastqs is None:
        # Set default to false
        defrost_archived_fastqs = False

    # Confirm that share type is of ShareTypeEnum
    if share_type is None:
        logger.error("Share type must be provided")
        raise ValueError("Share type must be provided")
    share_type = ShareTypeEnum(share_type)

    # Confirm that if share type is push, that share destination is provided
    if share_type == ShareTypeEnum.PUSH and share_destination is None:
        logger.error("Share destination must be provided if share type is push")
        raise ValueError("Share destination must be provided if share type is push")

    # Confirm that dryrun is a boolean value if not specified set to false
    if dryrun is None:
        dryrun = False

    # Confirm only one of library_id_list, subject_id_list, individual_id_list, project_id_list is provided
    if sum([library_id_list, subject_id_list, individual_id_list, project_id_list]) > 1:
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
        library_orcabus_id_list = list(map(
            lambda library_obj_iter: library_obj_iter["orcabusId"],
            list(set(list(reduce(
                concat,
                list(map(
                    lambda subject_iter_: list_libraries_in_subject(coerce_subject_id_or_orcabus_id_to_subject_orcabus_id(subject_iter_)),
                    subject_id_list
                ))
            ))))
        ))
    if individual_id_list is not None:
        library_orcabus_id_list = list(map(
            lambda library_obj_iter: library_obj_iter["orcabusId"],
            list(set(list(reduce(
                concat,
                list(map(
                    lambda individual_iter_: list_libraries_in_individual(coerce_individual_id_or_orcabus_id_to_individual_orcabus_id(individual_iter_)),
                    individual_id_list
                ))
            ))))
        ))
    if project_id_list is not None:
        library_orcabus_id_list = list(map(
            lambda library_obj_iter: library_obj_iter["orcabusId"],
            list(set(list(reduce(
                concat,
                list(map(
                    lambda project_iter_: list_libraries_in_project(coerce_project_id_or_orcabus_id_to_project_orcabus_id(project_iter_)),
                    project_id_list
                ))
            ))))
        ))

    # Coerce data types
    if data_type_list is None:
        logger.error("Data type list must be provided")
        raise ValueError("Data type list must be provided")
    data_type_list: List[DataTypeEnum] = list(set(list(map(
        lambda data_type_iter_: DataTypeEnum(data_type_iter_.lower()),
        data_type_list
    ))))

    # Secondary analysis data type list
    if secondary_analysis_workflow_list is not None:
        secondary_analysis_workflow_list: List[SecondaryAnalysisDataTypeEnum] = list(set(list(map(
            lambda secondary_analysis_workflow_iter_: SecondaryAnalysisDataTypeEnum(secondary_analysis_workflow_iter_.lower()),
            secondary_analysis_workflow_list
        ))))

    # Export the variables
    return {
        "libraryOrcabusIdList": library_orcabus_id_list,
        "instrumentRunIdList": instrument_run_id_list,
        "portalRunIdList": portal_run_id_list,
        "portalRunIdExclusionList": portal_run_id_exclusion_list,
        "shareType": share_type,
        "shareDestination": share_destination,
        "defrostArchivedFastqs": defrost_archived_fastqs,
        "dryrun": dryrun,
        "dataTypeList": list(map(lambda data_type_iter_: data_type_iter_.value, data_type_list)),
        "secondaryAnalysisWorkflowList": list(map(lambda secondary_analysis_workflow_iter_: secondary_analysis_workflow_iter_.value, secondary_analysis_workflow_list))
    }
