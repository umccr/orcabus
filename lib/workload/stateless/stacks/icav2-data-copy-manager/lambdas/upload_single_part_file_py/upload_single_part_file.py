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
import typing
from os import environ
from textwrap import dedent

import boto3

from wrapica.project_data import (
    ProjectData,
    get_aws_credentials_access_for_project_folder,
    create_download_url
)

from tempfile import NamedTemporaryFile
from subprocess import run

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
        
        wget \
         --quiet \
         --output-document /dev/stdout \
         "__PRESIGNED_URL__" | \
        aws s3 cp --expected-size "__FILE_SIZE_IN_BYTES__" - "__DESTINATION_PATH__"
        """
    )


def generate_shell_script(
        source_file_object: ProjectData,
        destination_folder_object: ProjectData,
):
    # Get presigned url from source file
    source_file_presigned_url = create_download_url(
        project_id=source_file_object.project_id,
        file_id=source_file_object.file_id,
    )

    # Get file size
    file_size = source_file_object.data.details.file_size_in_bytes

    temp_file_path = NamedTemporaryFile(delete=False, suffix=".sh").name

    with open(temp_file_path, "w") as temp_file_h:
        temp_file_h.write(
            get_shell_script_template().replace(
                "__PRESIGNED_URL__", source_file_presigned_url
            ).replace(
                "__FILE_SIZE_IN_BYTES__", str(file_size)
            ).replace(
                "__DESTINATION_PATH__", destination_folder_object.data.details.path
            ) + "\n"
        )

    return temp_file_path


def run_shell_script(
        shell_script_path: str,
        destination_credentials
):
    """
    Run the shell script with the following environment variables set
    :param shell_script_path:
    :param destination_credentials:
    :return:
    """
    proc = run(
        [
            "bash", shell_script_path
        ],
        env={
            **dict(environ),
            "AWS_ACCESS_KEY_ID": destination_credentials.access_key,
            "AWS_SECRET_ACCESS_KEY": destination_credentials.secret_key,
            "AWS_SESSION_TOKEN": destination_credentials.session_token,
            "AWS_REGION": destination_credentials.region
        },
        capture_output=True
    )

    if not proc.returncode == 0:
        raise RuntimeError(
            f"Failed to run shell script {shell_script_path} with return code {proc.returncode}. "
            f"Stdout was {proc.stdout.decode()}"
            f"Stderr was {proc.stderr.decode()}"
        )

    return


def hander(event, context):
    """
    Given the inputs of
    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    # Get the source file object
    source_object = ProjectData(
        project_id=event["sourceData"]["projectId"],
        file_id=event["sourceData"]["dataId"]
    )
    # Get the destination folder object
    destination_folder_object = ProjectData(
        project_id=event["destinationData"]["projectId"],
        file_id=event["destinationData"]["dataId"]
    )

    # Get the shell script
    shell_script_path = generate_shell_script(
        source_object,
        destination_folder_object
    )

    # Get destination credentials
    destination_credentials = get_aws_credentials_access_for_project_folder(
        project_id=destination_folder_object.project_id,
        folder_path=destination_folder_object.data.details.path
    )

    # Run the shell script
    run_shell_script(
        shell_script_path=shell_script_path,
        destination_credentials=destination_credentials
    )
