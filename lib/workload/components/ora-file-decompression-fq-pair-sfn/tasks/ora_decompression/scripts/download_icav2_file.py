#!/usr/bin/env python3

# Standard library imports
import sys
from pathlib import Path
from wrapica.project_data import (
    ProjectData,
    convert_uri_to_project_data_obj,
    write_icav2_file_contents
)


def main():
    # Get input
    input_uri = sys.argv[1]
    output_file = Path(sys.argv[2])

    # Step 1 - Convert URI to projectdata object
    project_data_obj: ProjectData = convert_uri_to_project_data_obj(input_uri)

    # Write project data object to file
    write_icav2_file_contents(
        project_data_obj.project_id,
        project_data_obj.data.details.path,
        output_file
    )


if __name__ == "__main__":
    main()
