#!/usr/bin/env python3

"""
Add run manifest
"""

# Standard libraries
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse, urlunparse

# Wrapica imports
from wrapica.libica_models import ProjectData
from wrapica.project_data import convert_project_data_obj_to_icav2_uri


def get_destination_uri_path(
    root_output_path: Path,
    output_project_id: str,
    output_folder_path: Path,
    file_path: Path
) -> str:
    """
    Get the destination uri path
    :param root_output_path: The root output path
    :param output_project_id: The output project id to extend the path to
    :param output_folder_path: The output folder path
    :param file_path: The file path
    :return: The destination uri path
    """
    # Get the output path relative to the root output
    # This is then extended onto the output folder path
    relative_file_path = Path(file_path).relative_to(root_output_path)

    # Get the output path (which is the parent directory)
    dest_uri_path = str(
        urlunparse((
            "icav2",
            output_project_id,
            str(output_folder_path.joinpath(relative_file_path).absolute().parent) + "/",
            None, None, None
        ))
    )

    return dest_uri_path


def get_dest_uri_from_src_uri(
        src_uri: str,
        root_output_path: Path,
        dest_project_id: str,
        dest_folder_path: Path
) -> str:
    """
    Get the destination uri path from the source uri path, use this for generating the fastq list rows
    :param src_uri: The source uri
    :param root_output_path: The root output path
    :param dest_project_id: The output project id to extend the path to
    :param dest_folder_path: The output folder path
    :return: The destination uri path
    """
    # Get the output path relative to the root output
    # This is then extended onto the output folder path
    relative_file_path = Path(urlparse(src_uri).path).relative_to(root_output_path)

    # Get the output path (which is the parent directory)
    dest_uri_path = str(
        urlunparse((
            "icav2",
            dest_project_id,
            str(dest_folder_path.joinpath(relative_file_path).absolute().parent) + "/",
            None, None, None
        ))
    )

    return dest_uri_path


def generate_run_manifest(
    root_run_uri: str,
    project_data_list: List[ProjectData],
    output_project_id: str,
    output_folder_path: Path
) -> Dict:
    """
    Generate run manifest
    :param root_run_uri: Use this to get the relative path for each file list to be added to the run manifest
    :param project_data_list: list of projectdata objects
    :param output_project_id: The output project id to extend the path to
    :param output_folder_path: Path
    :return: run manifest
    """
    
    # Get the root output path of the run
    root_output_path = Path(urlparse(root_run_uri).path)
    
    # Initialise the run manifest dictionary
    run_manifest_dict = {}

    for file_obj_iter in project_data_list:

        # Get the source file uri
        source_file_uri = convert_project_data_obj_to_icav2_uri(file_obj_iter)
        
        # Get the output path (which is the parent directory)
        dest_uri_path = get_destination_uri_path(
            root_output_path=root_output_path,
            output_project_id=output_project_id,
            output_folder_path=output_folder_path,
            file_path=file_obj_iter.data.details.path
        )

        # Add the source file uri to the run manifest dictionary
        run_manifest_dict[source_file_uri] = [
            dest_uri_path
        ]

    # Return the dictionary
    return run_manifest_dict
