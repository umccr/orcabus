#!/usr/bin/env python3

"""
Given an icav2 uri, find all the vcf files in the directory and return a list of the files.
"""

# Wrapica imports
from wrapica.enums import DataType
from wrapica.libica_models import ProjectData

from wrapica.project_data import (
    find_project_data_bulk,
    convert_icav2_uri_to_data_obj,
    convert_project_data_obj_to_icav2_uri
)


def handler(event, context):
    """
    Use the project data bulk command to find all vcf files in the directory and zip them all up
    :param event:
    :param context:
    :return:
    """

    icav2_uri = event.get("icav2_uri")

    data_obj: ProjectData = convert_icav2_uri_to_data_obj(icav2_uri)

    return {
        "vcf_icav2_uri_list": list(
            map(
                lambda project_data_iter: convert_project_data_obj_to_icav2_uri(project_data_iter),
                filter(
                    lambda project_data_iter: (
                            project_data_iter.data.details.path.endswith(".vcf") and
                            DataType[project_data_iter.data.type] == DataType.FILE
                    ),
                    find_project_data_bulk(
                        project_id=data_obj.project_id,
                        parent_folder_id=data_obj.data.id,
                        data_type=DataType.FILE
                    )
                )
            )
        )
    }
