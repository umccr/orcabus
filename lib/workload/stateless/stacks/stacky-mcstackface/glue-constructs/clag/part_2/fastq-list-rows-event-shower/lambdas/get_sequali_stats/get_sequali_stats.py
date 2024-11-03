#!/usr/bin/env python3

"""
This script is used to get the statistics of the sequali dataset.
"""
import json
from pathlib import Path

# Standard imports
import pandas as pd
import boto3
import typing
import logging
import tempfile
from os import environ
import subprocess
from urllib.parse import urlparse

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
HG38_N_BASES = 3099734149  #  https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000001405.26

SEQUALI_TEMPLATE_STR = """
#!/usr/bin/env bash

# Set up the environment
set -eu

# Globals
OUTPUT_DIRNAME="output"

# Glocals
S3_R1_FILE_NAME="__S3_R1_FILE_NAME__"
S3_R2_FILE_NAME="__S3_R2_FILE_NAME__"
S3_R1_PRESIGNED_URL="__S3_R1_PRESIGNED_URL__"
S3_R2_PRESIGNED_URL="__S3_R2_PRESIGNED_URL__"

# Create a directory to store the output
mkdir -p "${OUTPUT_DIRNAME}"

# Download the first 1 million reads for the R1 file
wget \
  --quiet \
  --output-document /dev/stdout \
  "${S3_R1_PRESIGNED_URL}" | \
zcat | \
head -n4000000 | \
gzip --stdout > "${S3_R1_FILE_NAME%.fastq.gz}_subset.fastq.gz"

# Download the first 1 million reads for the R2 file
wget \
  --quiet \
  --output-document /dev/stdout \
  "${S3_R2_PRESIGNED_URL}" | \
zcat | \
head -n4000000 | \
gzip --stdout > "${S3_R2_FILE_NAME%.fastq.gz}_subset.fastq.gz"

# Import the reads into sequali
sequali \
  --outdir "${OUTPUT_DIRNAME}" \
  --json "output.json" \
  "${S3_R1_FILE_NAME%.fastq.gz}_subset.fastq.gz" \
  "${S3_R2_FILE_NAME%.fastq.gz}_subset.fastq.gz"
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


def get_insert_size_estimate(insert_sizes: List[int]) -> float:
    """
    Given a list, return the weighted average
    :param insert_sizes:
    :return:
    """

    # Get the weighted average
    # Dont include '0' insert sizes
    insert_size_estimate = sum(
        [
            insert_size * insert_size_count
            for insert_size, insert_size_count in enumerate(insert_sizes)
            if insert_size > 0
        ]
    ) / sum(insert_sizes[1:])

    return round(insert_size_estimate, 2)


def run_sequali(r1_fastq_url: str, r2_fastq_url: str, read_count: int) -> Dict[str, str]:
    """
    Run sequali through the template shell script
    :param r1_fastq_url:
    :param r2_fastq_url:
    :param read_count:
    :return:
    """
    # Create a copy of the shell script
    with tempfile.NamedTemporaryFile(suffix=".sh") as temp_file_obj:
        # Copy the template to the temp file
        filedata = SEQUALI_TEMPLATE_STR

        # Replace
        filedata = filedata.replace("__S3_R1_FILE_NAME__", Path(urlparse(r1_fastq_url).path).name)
        filedata = filedata.replace("__S3_R2_FILE_NAME__", Path(urlparse(r2_fastq_url).path).name)
        filedata = filedata.replace("__S3_R1_PRESIGNED_URL__", r1_fastq_url)
        filedata = filedata.replace("__S3_R2_PRESIGNED_URL__", r2_fastq_url)

        # Write back
        with open(temp_file_obj.name, "w") as file_h:
            file_h.write(filedata)

        # Run the sequali command in a temp directory
        working_dir = tempfile.TemporaryDirectory()

        # Run the sequali command
        sequali_proc = subprocess.run(
            ["bash", temp_file_obj.name],
            cwd=working_dir.name,
            capture_output=True
        )

        if not sequali_proc.returncode == 0:
            # Log the output
            logger.error("Sequali command failed")
            logger.error("Stdout: '%s'", sequali_proc.stdout.decode())
            logger.error("Stderr: '%s'", sequali_proc.stderr.decode())

            # Raise the error
            raise ChildProcessError

        # Get the sequali output
        sequali_output = Path(working_dir.name) / "output" / "output.json"

        # Read the file into a pandas dataframe
        with open(sequali_output, "r") as file_h:
            sequali_output_dict = json.load(file_h)

        # Convert to a dataframe
        sequali_summary_df = (
            pd.DataFrame(
                {
                    "r1": sequali_output_dict['summary'],
                    "r2": sequali_output_dict['summary_read2']
                }
            )
            .transpose()
            .reset_index()
            # Get q20 fraction
            .assign(
                q20_pct=lambda x: round(x['q20_bases'] / x['total_bases'], 2),
                gc_pct=lambda x: round(x['total_gc_bases'] / x['total_bases'], 2)
            )
            # Drop columns related to total values (this is just a summary of the first million reads)
            .drop(
                columns=[
                    "total_reads", "total_bases",
                    "q20_reads", "q20_bases",
                    "total_gc_bases", "total_n_bases"
                ]
            )
        )

        # Calculate the insert size estimate
        insert_size_estimate = get_insert_size_estimate(sequali_output_dict['insert_size_metrics']['insert_sizes'])

        # Get the duplicate fraction metric
        duplicate_fraction = round(1.0 - sequali_output_dict['duplication_fractions']['remaining_fraction'], 2)

        return {
            # Insert Size Estimate and Duplicate Fraction
            "insert_size_estimate": insert_size_estimate,
            "duplicate_fraction": duplicate_fraction,
            "estimated_bases": (
                int(sequali_summary_df['mean_length'].sum() * read_count)
            ),
            "estimated_wgs_cov": round(sequali_summary_df['mean_length'].sum() * read_count / HG38_N_BASES, 2),
            # R1 Mean length
            "r1_mean_length": round(sequali_summary_df.query('index=="r1"')['mean_length'].item(), 2),
            "r2_mean_length": round(sequali_summary_df.query('index=="r2"')['mean_length'].item(), 2),
            # Min Read Length
            "r1_min_read_length": round(sequali_summary_df.query('index=="r1"')['minimum_length'].item(), 2),
            "r2_min_read_length": round(sequali_summary_df.query('index=="r2"')['minimum_length'].item(), 2),
            # Max Read Length
            "r1_max_read_length": round(sequali_summary_df.query('index=="r1"')['maximum_length'].item(), 2),
            "r2_max_read_length": round(sequali_summary_df.query('index=="r2"')['maximum_length'].item(), 2),
            # Q20 Fraction
            "r1_q20_frac": round(sequali_summary_df.query('index=="r1"')['q20_pct'].item(), 2),
            "r2_q20_frac": round(sequali_summary_df.query('index=="r2"')['q20_pct'].item(), 2),
            # GC Fraction
            "r1_gc_frac": round(sequali_summary_df.query('index=="r1"')['gc_pct'].item(), 2),
            "r2_gc_frac": round(sequali_summary_df.query('index=="r2"')['gc_pct'].item(), 2),
        }


def handler(event, context):
    """
    Given a sequali url, create a copy of the sequali template and replace __S3_PRESIGNED_URL__ with the url to the fastq file

    Then run the sequali command

    Extract the relevant outputs from the sequali output and return them in json format
    :param event:
    :param context:
    :return:
    """

    # Set the icav2 environment variables
    set_icav2_env_vars()

    # Get the uri
    read_count = event['read_count']
    read1_uri = event['read1_fastq_uri']
    read2_uri = event['read2_fastq_uri']

    # Check read count is not zero
    if read_count == 0:
        return {
            "sequali_rapid_summary": None
        }

    # Get the uri as a project data object
    read1_projectdata_obj: ProjectData = convert_uri_to_project_data_obj(read1_uri)
    read2_projectdata_obj: ProjectData = convert_uri_to_project_data_obj(read2_uri)

    # Create the download url
    read1_download_url = create_download_url(
        read1_projectdata_obj.project_id,
        read1_projectdata_obj.data.id
    )
    read2_download_url = create_download_url(
        read2_projectdata_obj.project_id,
        read2_projectdata_obj.data.id
    )

    # Run sequali
    sequali_output = run_sequali(read1_download_url, read2_download_url, read_count)

    return {
        "sequali_rapid_summary": sequali_output
    }

# if __name__ == "__main__":
#     # Set environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-production"
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "read1_fastq_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/240926_A01052_0232_AHW7LHDSXC/20240928f63332ac/Samples/Lane_1/L2401325/L2401325_S1_L001_R1_001.fastq.gz",
#                     "read2_fastq_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/240926_A01052_0232_AHW7LHDSXC/20240928f63332ac/Samples/Lane_1/L2401325/L2401325_S1_L001_R2_001.fastq.gz"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "sequali_rapid_summary": {
#     #         "insert_size_estimate": 167.32,
#     #         "duplicate_fraction": 0.18,
#     #         "r1_mean_length": 141.8,
#     #         "r2_mean_length": 141.79,
#     #         "r1_min_read_length": 35,
#     #         "r2_min_read_length": 35,
#     #         "r1_max_read_length": 143,
#     #         "r2_max_read_length": 143,
#     #         "r1_q20_frac": 0.98,
#     #         "r2_q20_frac": 0.97,
#     #         "r1_gc_frac": 0.5,
#     #         "r2_gc_frac": 0.5
#     #     }
#     # }