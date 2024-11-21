#!/usr/bin/env python3

# Standard library imports
import sys
from wrapica.project_data import (
    ProjectData,
    convert_uri_to_project_data_obj,
    create_download_url
)


def main():
    # Get input
    input_uri = sys.argv[1]

    # Step 1 - Convert URI to projectdata object
    project_data_obj: ProjectData = convert_uri_to_project_data_obj(input_uri)

    # Write project data object to file
    print(
        create_download_url(
            project_data_obj.project_id,
            project_data_obj.data.id
        )
    )


if __name__ == "__main__":
    main()
