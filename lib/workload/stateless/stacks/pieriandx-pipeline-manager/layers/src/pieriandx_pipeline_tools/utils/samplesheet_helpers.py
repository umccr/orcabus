#!/usr/bin/env python

# Standard imports
from typing import Dict
from pathlib import Path
from tempfile import NamedTemporaryFile

# Custom imports
from wrapica.project_data import (
    read_icav2_file_contents, convert_uri_to_project_data_obj,
    ProjectData
)
from v2_samplesheet_maker.functions.v2_samplesheet_reader import v2_samplesheet_reader


def read_v2_samplesheet(samplesheet_uri: str) -> Dict:
    """
    Read in a v2 samplesheet from the given uri and return as a dictionary

    Args:
        samplesheet_uri: Path to the samplesheet s3 or icav2 uri

    Returns:

    """

    # Initialise tempfile object
    temp_file = NamedTemporaryFile(suffix=".csv")

    # Get samplesheet uri as an icav2 projectdata object
    icav2_project_data_obj: ProjectData = convert_uri_to_project_data_obj(samplesheet_uri)

    # Write icav2 file contents to temp file
    read_icav2_file_contents(
        icav2_project_data_obj.project_id,
        icav2_project_data_obj.data.id,
        output_path=Path(temp_file.name)
    )

    # Read the v2 samplesheet from the temp file
    return v2_samplesheet_reader(
        Path(temp_file.name)
    )
