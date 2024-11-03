#!/usr/bin/env python3

"""
Given a url to a fastq file, create a copy of the fastqc template
"""

from pathlib import Path

# Standard imports
import pandas as pd
import boto3
import typing
import logging
import tempfile
from os import environ
import shutil
import subprocess

# Wrapica
from wrapica.project_data import (
    ProjectData, create_download_url, convert_uri_to_project_data_obj
)

# Type checking
from typing import Dict, List
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"
FASTQC_TEMPLATE = """
#!/usr/bin/env bash

# Set up the environment
set -eu

# Globals
OUTPUT_DIRNAME="outdir"

# Glocals
S3_PRESIGNED_URL="__S3_PRESIGNED_URL__"

# Create a directory to store the output
mkdir -p "${OUTPUT_DIRNAME}"

# Download the file from S3,
# extract the first 4M lines (1 million reads),
# and run FastQC
wget \
  --quiet \
  --output-document /dev/stdout \
  "${S3_PRESIGNED_URL}" | \
zcat | \
head -n4000000 | \
fastqc \
  --extract \
  --outdir outdir \
  --format fastq \
  --quiet \
  "stdin" 1>/dev/null 2>&1

# Print the summary to stdout
cat outdir/stdin_fastqc/summary.txt
"""

# Set loggers
logging.basicConfig(
    level=logging.INFO,
    force=True,
    format='%(asctime)s %(message)s'
)
logger = logging.getLogger()

def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_secret(secret_id: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_id)["SecretString"]


# Functions
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )

def run_fastqc(fastq_url: str) -> List[Dict[str, str]]:
    """
    Run fastqc through the template shell script

    PASS    Basic Statistics        stdin
    PASS    Per base sequence quality       stdin
    PASS    Per tile sequence quality       stdin
    PASS    Per sequence quality scores     stdin
    WARN    Per base sequence content       stdin
    PASS    Per sequence GC content stdin
    PASS    Per base N content      stdin
    WARN    Sequence Length Distribution    stdin
    WARN    Sequence Duplication Levels     stdin
    PASS    Overrepresented sequences       stdin
    PASS    Adapter Content stdin

    :param fastq_url:
    :return:
    """
    # Create a copy of the shell script
    with tempfile.NamedTemporaryFile(suffix=".sh") as temp_file_obj:
        # Copy the template to the temp file
        filedata = FASTQC_TEMPLATE

        # Replace the __S3_PRESIGNED_URL__ with the fastq url
        filedata = filedata.replace("__S3_PRESIGNED_URL__", fastq_url)
        with open(temp_file_obj.name, "w") as file_h:
            file_h.write(filedata)

        # Run the fastqc command in a temp directory
        working_dir = tempfile.TemporaryDirectory()

        # Run the fastqc command
        run_fastqc_proc = subprocess.run(
            ["bash", temp_file_obj.name],
            cwd=working_dir.name,
            capture_output=True
        )

    if not run_fastqc_proc.returncode == 0:
        logger.error(f"Run FastQC Proc failed with return code {run_fastqc_proc.returncode}")
        logger.error(f"Run FastQC Proc failed with stderr {run_fastqc_proc.stderr.decode()}")
        logger.error(f"Run FastQC Proc failed with stdout {run_fastqc_proc.stdout.decode()}")
        raise ChildProcessError

    # Get the fastqc output
    fastqc_output_str = run_fastqc_proc.stdout.decode()

    # Parse the fastqc output to a pandas dataframe
    # Easiest to just create another temp file, write the output to that file, and then read it into a pandas dataframe
    with tempfile.NamedTemporaryFile(suffix=".tsv") as temp_file_obj:
        with open(temp_file_obj.name, "w") as file_h:
            file_h.write(fastqc_output_str)

        # Read the file into a pandas dataframe
        fastqc_output_df = pd.read_csv(
            temp_file_obj.name,
            sep="\t",
            names=["status", "metric", "stdin"]
        ).drop(columns=["stdin"])

    # Convert metric from spaces to snake case
    fastqc_output_df["metric"] = fastqc_output_df["metric"].str.replace(" ", "_")

    # Return as a dict
    return fastqc_output_df.to_dict(orient="records")


def handler(event, context):
    """
    Given a fastqc url, create a copy of the fastqc template and replace __S3_PRESIGNED_URL__ with the url to the fastq file

    Then run the fastqc command

    Extract the relevant outputs from the fastqc output and return them in json format
    :param event:
    :param context:
    :return:
    """

    # Set the icav2 environment variables
    set_icav2_env_vars()

    # Get the uri
    uri = event['fastq_uri']

    read_count = event['read_count']

    ## Check if the read count is greater than 0
    if read_count == 0:
        return {
            "fastqc_output": None
        }

    # Get the uri as a project data object
    fastqc_projectdata_obj: ProjectData = convert_uri_to_project_data_obj(uri)

    # Create the download url
    fastqc_download_url = create_download_url(
        fastqc_projectdata_obj.project_id,
        fastqc_projectdata_obj.data.id
    )

    # Run fastqc
    fastqc_output = run_fastqc(fastqc_download_url)

    return {
        "fastqc_output": fastqc_output
    }


# if __name__ == "__main__":
#     # Test the function
#     import json
#     from os import environ
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     environ['AWS_REGION'] = "ap-southeast-2"
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['PATH'] = environ['PATH'] + ':/home/alexiswl/miniconda3/envs/biotools/bin'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "fastq_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )