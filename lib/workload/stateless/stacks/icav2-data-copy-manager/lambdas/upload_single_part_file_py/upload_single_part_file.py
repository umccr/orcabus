#!/usr/bin/env python3

"""
Upload a single part file to S3 using the boto3 library.

Rather than download + upload we perform the following steps:

1. Get AWS credentials for the parent directory

2. Get the file size of the file to be uploaded

3. Generate a presigned URL for the file to be downloaded

4. Create a temp shell script with the following template:

'
#!/usr/bin/env bash

set -euo pipefail

wget \
 --quiet \
 --output-document /dev/stdout \
 "{__PRESIGNED_URL__}" | \
aws s3 cp --expected-size "${__FILE_SIZE_IN_BYTES__}" - "${__DESTINATION_PATH__}"
'

We then run the shell script through subprocess.run with the following environment variables set

1. AWS_ACCESS_KEY_ID - the access key id for this destination path
2. AWS_SECRET_ACCESS_KEY - the secret access key for this destination path
3. AWS_SESSION_TOKEN - the session token for this destination path

We take in the following inputs:

{
    "sourceData": {
      "projectId": "abcdefghijklmnop",
      "dataId": "fil.abcdefghijklmnop",
    }
    "destinationData": {
      "projectId": "abcdefghijklmnop",
      "dataId": "fil.abcdefghijklmnop",
    }
}
"""
import json
import typing
from os import environ
from pathlib import Path
from textwrap import dedent
import requests

import boto3
from wrapica.enums import DataType

from wrapica.project_data import (
    create_download_url,
    get_project_data_obj_by_id,
    get_project_data_obj_from_project_id_and_path
)

from tempfile import NamedTemporaryFile
from subprocess import run

from wrapica.utils.configuration import get_icav2_access_token

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient


# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


# AWS things
def get_ssm_client() -> 'SSMClient':
    """
    Return SSM client
    """
    return boto3.client("ssm")


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_ssm_parameter_value(parameter_path) -> str:
    """
    Get the ssm parameter value from the parameter path
    :param parameter_path:
    :return:
    """
    return get_ssm_client().get_parameter(Name=parameter_path)["Parameter"]["Value"]


def get_secret(secret_arn: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_arn)["SecretString"]


# Set the icav2 environment variables
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def get_shell_script_template() -> str:
    return dedent(
        """
        #!/usr/bin/env bash

        set -euo pipefail
        
        curl --location \
         "__DOWNLOAD_PRESIGNED_URL__" | \
        curl --location \
          --request PUT \
          --header 'Content-Type: application/octet-stream' \
          --data-binary "@-" \
          "__UPLOAD_PRESIGNED_URL__"
        """
    )


def generate_shell_script(
        source_file_download_url: str,
        destination_file_upload_url: str,
):
    # Create a temp file
    temp_file_path = NamedTemporaryFile(
        delete=False,
        suffix=".sh"
    ).name

    # Write the shell script to the temp file
    with open(temp_file_path, "w") as temp_file_h:
        temp_file_h.write(
            get_shell_script_template().replace(
                "__DOWNLOAD_PRESIGNED_URL__", source_file_download_url
            ).replace(
                "__UPLOAD_PRESIGNED_URL__", destination_file_upload_url
            ) + "\n"
        )

    return temp_file_path


def create_file_with_upload_url(
        project_id: str,
        folder_id: str,
        file_name: str,
) -> str:
    # Set headers
    headers = {
        'Accept': 'application/vnd.illumina.v3+json',
        'Content-Type': 'application/vnd.illumina.v3+json',
        'Authorization': f"Bearer {get_icav2_access_token()}"
    }

    data = {
        "name": file_name,
        "folderId": folder_id,
    }

    response = requests.post(
        f'https://ica.illumina.com/ica/rest/api/projects/{project_id}/data:createFileWithUploadUrl',
        headers=headers,
        data=json.dumps(data),
    )

    response.raise_for_status()

    return response.json()['uploadUrl']


def run_shell_script(
        shell_script_path: str,
):
    """
    Run the shell script with the following environment variables set
    :param shell_script_path:
    :return:
    """
    proc = run(
        [
            "bash", shell_script_path
        ],
        capture_output=True
    )

    if not proc.returncode == 0:
        raise RuntimeError(
            f"Failed to run shell script {shell_script_path} with return code {proc.returncode}. "
            f"Stdout was {proc.stdout.decode()}"
            f"Stderr was {proc.stderr.decode()}"
        )

    return


def handler(event, context):
    """
    Given the inputs of
    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    # Get the source file object
    source_object = get_project_data_obj_by_id(
        project_id=event["sourceData"]["projectId"],
        data_id=event["sourceData"]["dataId"]
    )
    # Get the destination folder object
    destination_folder_object = get_project_data_obj_by_id(
        project_id=event["destinationData"]["projectId"],
        data_id=event["destinationData"]["dataId"]
    )

    # Create the source file download url
    source_file_download_url = create_download_url(
        project_id=source_object.project_id,
        file_id=source_object.data.id,
    )

    # Check if the destination file exists
    try:
        _ = get_project_data_obj_from_project_id_and_path(
            project_id=destination_folder_object.project_id,
            data_path=Path(destination_folder_object.data.details.path) / source_object.data.details.name,
            data_type=DataType.FILE
        )
        return
    except FileNotFoundError:
        pass
    # Create the file object
    destination_file_upload_url = create_file_with_upload_url(
        project_id=destination_folder_object.project_id,
        folder_id=destination_folder_object.data.id,
        file_name=source_object.data.details.name
    )

    # Get the shell script
    shell_script_path = generate_shell_script(
        source_file_download_url,
        destination_file_upload_url
    )

    # Run the shell script
    run_shell_script(
        shell_script_path=shell_script_path,
    )


# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ["ICAV2_ACCESS_TOKEN_SECRET_ID"] = "ICAv2JWTKey-umccr-prod-service-production"
#
#     print(json.dumps(
#         handler(
#             {
#                 "sourceData": {
#                     "projectId": "eba5c946-1677-441d-bbce-6a11baadecbb",
#                     "dataId": "fil.be1b0cc74abe44c919a008dd6f300f84"
#                 },
#                 "destinationData": {
#                     "projectId": "6f123cb4-cbd2-46a8-82a8-d91dcb608817",
#                     "dataId": "fol.2379160ba4884949471008dd77d4a93c"
#                 }
#             },
#             None)
#         , indent=4
#     ))
#
#     # null