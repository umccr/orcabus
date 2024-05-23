#!/usr/bin/env python3

"""
Handle the analysis object

"""

# Imports
import gzip
import json
from base64 import b64encode
from pathlib import Path
from typing import Dict, Tuple, List, Union
from bssh_manager_tools.utils.samplesheet_helper import read_v2_samplesheet
import logging

# Wrapica imports
from wrapica.project_data import (
    read_icav2_file_contents_to_string
)

from wrapica.libica_models import (
    ProjectData
)
from wrapica.project_data import (
    find_project_data_bulk,
    get_file_by_file_name_from_project_data_list, get_project_data_obj_by_id,
)
from wrapica.project_analysis import (
    get_analysis_output_object_from_analysis_code
)
from wrapica.enums import DataType

# Local libraries
from ..runinfo import get_run_id_from_run_info

# Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_bclconvert_outputs_from_analysis_id(
    project_id: str,
    analysis_id: str
) -> Tuple[str, List[ProjectData]]:

    bclconvert_output_folder_id = get_analysis_output_object_from_analysis_code(
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


def get_basespace_run_id_from_bssh_json_output(bssh_json_output: Dict) -> int:
    """
    From
    {
      ...
      "Projects": {
        "OutputProject": {
          "Name": "bssh_aps2-sh-prod_3593591"
        }
      }
    }

    To

    3593591
    :param bssh_json_output:
    :return:
    """
    return int(
        bssh_json_output
        .get("Projects")
        .get("OutputProject")
        .get("Name")
        .split("_")[-1]
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


def get_samplesheet_file_id_from_analysis_output_list(analysis_output: List[ProjectData]) -> str:
    return get_file_by_file_name_from_project_data_list("SampleSheet.csv", analysis_output).data.id


def compress_dict(input_dict: Union[Dict, List]) -> str:
    """
    Given a json input, compress to a base64 encoded string

    param: input_dict: input dictionary to compress

    Returns: gzipped compressed base64 encoded string
    """

    # Compress
    return b64encode(
        gzip.compress(
            json.dumps(input_dict).encode('utf-8')
        )
    ).decode("utf-8")


def collect_analysis_objects(project_id: str, analysis_id: str) -> Dict:
    """
    Given a project id and analysis id for bclconvert runs,
    Collect the samplesheet and run info xml objects
    """

    # Get the analysis output path
    logger.info("Collecting output data objects")
    bclconvert_output_folder_id, bclconvert_output_data_list = get_bclconvert_outputs_from_analysis_id(
        project_id=project_id,
        analysis_id=analysis_id
    )

    # Get the output folder object
    logger.info("Get bclconvert output folder object")
    bclconvert_output_folder_obj = get_project_data_obj_by_id(
        project_id=project_id,
        data_id=bclconvert_output_folder_id
    )

    # Get the bssh_json
    logger.info("Collecting bssh json file id")
    bssh_output_file_id = get_bssh_json_file_id_from_analysis_output_list(bclconvert_output_data_list)

    # Read the json object
    bssh_json_dict = json.loads(
        read_icav2_file_contents_to_string(
            project_id=project_id,
            data_id=bssh_output_file_id
        )
    )

    # Now we have the bsshoutput.json, we can filter the output_data_list to just be those under 'output/'
    # We also collect the bcl convert output object to get relative files from this directory
    # Such as the IndexMetricsOut.bin file in the Reports Directory
    # Which we also copy over to the interops directory
    bcl_convert_output_path = Path(bclconvert_output_folder_obj.data.details.path) / "output"
    bclconvert_output_data_list = list(
        filter(
            lambda data_obj:
                (
                    # File is inside 'output' directory
                    data_obj.data.details.path.startswith(
                        str(bcl_convert_output_path) + "/"
                    ) and not (
                        # File is not the fastq_list_s3.csv or TSO500L_fastq_list_s3.csv
                        # This file is just a list of presigned urls that will expire in a week
                        data_obj.data.details.name.endswith("fastq_list_s3.csv")
                    )
                ),
            bclconvert_output_data_list
        )
    )

    # Get the basespace run id from the bssh output dict
    logger.info("Collecting basespace run id")
    basespace_run_id = get_basespace_run_id_from_bssh_json_output(bssh_json_dict)

    # Get run info (to collect the run id)
    logger.info("Collecting the run info xml file")
    run_info_file_id = get_run_info_xml_file_id_analysis_output_list(
        analysis_output=bclconvert_output_data_list
    )

    # Get the run id from the run info file id
    logger.info("Collecting the run id from the run info xml file")
    run_id = get_run_id_from_run_info(project_id, run_info_file_id)

    # Get the samplesheet file id
    logger.info("Collecting the samplesheet csv file")
    samplesheet_file_id = get_samplesheet_file_id_from_analysis_output_list(
        analysis_output=bclconvert_output_data_list
    )

    # We read in the samplesheet and return it as an output
    logger.info("Reading in the samplesheet")
    samplesheet_dict = read_v2_samplesheet(
        project_id=project_id,
        data_id=samplesheet_file_id
    )

    return {
        "instrument_run_id": run_id,
        "basespace_run_id": basespace_run_id,
        "samplesheet_b64gz": compress_dict(samplesheet_dict),
    }
