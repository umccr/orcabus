#!/usr/bin/env python3

"""
Get the output objects from the analysis id
"""

# Standard libraries
from typing import List, Tuple
from pathlib import Path

# UMCCR Libraries
from wrapica.libica_models import (
    AnalysisInput,
    ProjectData
)
from wrapica.project_data import (
    find_project_data_bulk,
    get_file_by_file_name_from_project_data_list, get_project_data_obj_by_id,
    get_project_data_folder_id_from_project_id_and_path, list_project_data_non_recursively
)
from wrapica.project_analysis import (
    get_analysis_input_object_from_analysis_input_code,
    get_analysis_output_object_from_analysis_output_code
)
from wrapica.enums import DataType

# Local libraries
from .logger import get_logger


# Set logger
logger = get_logger()


def get_interop_files_from_run_folder(
    run_folder_obj: ProjectData,
) -> List[ProjectData]:
    """
    Get the interop files from the run folder

    :param run_folder_obj:
    :param input_data_list:

    :return:
    """

    # Get the interop directory ID
    interop_directory_id = get_project_data_folder_id_from_project_id_and_path(
        project_id=run_folder_obj.project_id,
        folder_path=Path(run_folder_obj.data.details.path) / "InterOp"
    )

    # Return all files inside the interop directory
    return list(
        filter(
            lambda interop_iter: interop_iter.data.details.name.endswith(".bin"),
            list_project_data_non_recursively(
                project_id=run_folder_obj.project_id,
                parent_folder_id=interop_directory_id,
                data_type=DataType.FILE
            )
        )
    )


def get_run_folder_obj_from_analysis_id(project_id: str, analysis_id: str) -> ProjectData:
    """
    Query the outputs object from analysis id
    """

    run_folder_input: AnalysisInput = get_analysis_input_object_from_analysis_input_code(
        project_id,
        analysis_id,
        "run_folder"
    )

    # Get the folder ID
    run_folder_id = run_folder_input.analysis_data[0].data_id

    # Return all files recursively
    return get_project_data_obj_by_id(project_id, run_folder_id)


def get_bclconvert_outputs_from_analysis_id(
    project_id: str,
    analysis_id: str
) -> Tuple[str, List[ProjectData]]:

    bclconvert_output_folder_id = get_analysis_output_object_from_analysis_output_code(
        project_id,
        analysis_id,
        "Output"
    ).data[0].data_id

    # Return all files recursively
    return bclconvert_output_folder_id, find_project_data_bulk(
        project_id=project_id,
        parent_folder_id=bclconvert_output_folder_id,
        data_type=DataType.FILE
    )


def get_bssh_json_file_id_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    """
    Get the bssh json file id from the analysis output object
    :param analysis_output: 
    :return: 
    """
    return get_file_by_file_name_from_project_data_list("bsshoutput.json", analysis_output).data.id


def get_run_info_xml_file_id_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_by_file_name_from_project_data_list("RunInfo.xml", analysis_output).data.id


def get_samplesheet_path_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_by_file_name_from_project_data_list("SampleSheet.csv", analysis_output).data.details.path


def get_samplesheet_file_id_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_by_file_name_from_project_data_list("SampleSheet.csv", analysis_output).data.id


def get_fastq_list_csv_file_id_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_by_file_name_from_project_data_list("fastq_list.csv", analysis_output).data.id