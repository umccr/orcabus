#!/usr/bin/env python3

# Standard library imports
import sys
from pathlib import Path
import json

# Wrapica imports
from wrapica.project_data import (
    ProjectData,
    convert_uri_to_project_data_obj,
    get_project_data_folder_id_from_project_id_and_path,
    get_aws_credentials_access_for_project_folder
)
from wrapica.libica_models import AwsTempCredentials


def main():
    # Get input
    output_uri_dir = sys.argv[1]

    # Step 1 - Convert URI to project data object
    project_data_folder_obj: ProjectData = convert_uri_to_project_data_obj(
        output_uri_dir,
        create_data_if_not_found=True
    )

    # Step 3 - Get AWS credentials access
    aws_temp_credentials_access: AwsTempCredentials = get_aws_credentials_access_for_project_folder(
        project_data_folder_obj.project_id,
        project_data_folder_obj.data.id
    )

    # Write project data object to file
    print(
        json.dumps(
            {
                "AWS_ACCESS_KEY_ID": aws_temp_credentials_access.access_key,
                "AWS_SECRET_ACCESS_KEY": aws_temp_credentials_access.secret_key,
                "AWS_SESSION_TOKEN": aws_temp_credentials_access.session_token,
                "AWS_REGION": aws_temp_credentials_access.region
            },
            indent=4
        )
    )


if __name__ == "__main__":
    main()
