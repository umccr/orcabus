#!/usr/bin/env python3

"""
Get the output objects from the analysis id
"""
from typing import List, Tuple

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.project_analysis_api import ProjectAnalysisApi
from libica.openapi.v2.model.analysis_data import AnalysisData
from libica.openapi.v2.model.analysis_output import AnalysisOutput
from libica.openapi.v2.model.analysis_output_list import AnalysisOutputList
from libica.openapi.v2.model.project_data import ProjectData

from .icav2_configuration_handler import get_icav2_configuration
from .icav2_project_data_handler import find_data_recursively
from .logger import get_logger

logger = get_logger()


def get_outputs_object_from_analysis_id(project_id: str, analysis_id: str) -> Tuple[str, List[ProjectData]]:
    """
    Query the outputs object from analysis id
    """

    # Get configuration
    configuration = get_icav2_configuration()

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = ProjectAnalysisApi(api_client)

        # example passing only required values which don't have defaults set
        try:
            # Retrieve the outputs of an analysis.
            analysis_output: List[AnalysisOutput] = api_instance.get_analysis_outputs(
                project_id, analysis_id
            ).items
        except ApiException as e:
            logger.error("Exception when calling ProjectAnalysisApi->get_analysis_outputs: %s\n" % e)
            raise ApiException

        try:
            output_obj: AnalysisOutput = next(
                filter(
                    lambda analysis_iter: analysis_iter.code == "Output",
                    analysis_output
                )
            )
        except StopIteration:
            logger.error(f"Could not get output item from analysis {analysis_id}")
            raise StopIteration

        if not len(output_obj.data) == 1:
            logger.error(f"Expected analysis output data to be 1 but got {len(output_obj.data)}")
            raise ValueError

        # Get the folder ID
        analysis_folder_id = output_obj.data[0].data_id

        # Return all files recursively
        return analysis_folder_id, find_data_recursively(
            project_id=project_id,
            parent_folder_id=analysis_folder_id,
            name=".*",
            data_type="FILE",
            mindepth=None,
            maxdepth=None
        )


def get_file_from_project_data_list(project_data_list: List[ProjectData], file_name: str) -> ProjectData:
    """
    Get the file from the analysis output object
    :param analysis_output:
    :param file_name:
    :return:
    """

    # Find the first file with this name
    try:
        return next(
            filter(
                lambda file_iter: file_iter.data.details.name == file_name,
                project_data_list
            )
        )
    except StopIteration:
        logger.error(f"Could not get file {file_name} from analysis output")
        raise ValueError


def get_bssh_json_file_id_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    """
    Get the bssh json file id from the analysis output object
    :param analysis_output: 
    :return: 
    """
    return get_file_from_project_data_list(analysis_output, "bssh_output.json").data.id


def get_run_info_xml_file_id_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_from_project_data_list(analysis_output, "RunInfo.xml").data.id


def get_samplesheet_path_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_from_project_data_list(analysis_output, "SampleSheet.csv").data.details.path


def get_fastq_list_csv_file_id_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_from_project_data_list(analysis_output, "fastq_list.csv").data.details.path
