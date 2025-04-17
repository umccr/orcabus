#!/usr/bin/env python3

"""
SFN LAMBDA FUNCTION PLACEHOLDER: __create_script_from_presigned_urls_list_lambda_function_arn__

Given a list of presigned url objects, generate a script that downloads the files from the urls.

METADATA TO ADD TO EACH FILE:
- library ids
- primaryAnalysisType
- secondaryAnalysisType
- portalRunId
"""

import typing
import boto3
from pathlib import Path
from textwrap import dedent
from typing import List, Dict, Tuple
from directory_tree import DisplayTree
from tempfile import TemporaryDirectory
from humanfriendly import format_size
from urllib.parse import urlparse

from data_sharing_tools import (
    FileObjectWithPresignedUrlTypeDef,
    get_file_objects_with_presigned_urls
)

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_s3_client() -> "S3Client":
    return boto3.client('s3')


def get_bucket_key_tuple_from_s3_uri(s3_uri: str) -> Tuple[str, str]:
    s3_obj = urlparse(s3_uri)
    return s3_obj.netloc, s3_obj.path.lstrip('/')


def upload_file(file_contents: str, s3_uri: str):
    bucket, key = get_bucket_key_tuple_from_s3_uri(s3_uri)
    get_s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=file_contents,
    )


def get_script_template(
        file_count: int,
        total_data_size: int,
        display_tree: str
):
    """
    Head of Shell script for the client to use to download their data,
    Following needs to be replaced:

    __FILE_COUNT__
    __TOTAL_DATA_SIZE__
    __PRINT_TREE__


    :return:
    """

    return dedent("""
    #!/usr/bin/env bash

    : '
    This scripts is used to download data from the AWS s3 bucket with presigned urls
    '

    # Set to fail
    set -euo pipefail

    # Get the help command
    function print_help() {
        echo "
    Usage: download-data.sh (--download-path local/download_path/)
                            [--dryrun]
                            [-h | --help]

    Options:
      --download-path  The local path to download the data to, folders may be created underneath this path.
      --dryrun         If set, the script will only detail the files that will be downloaded, but will not download them.
      --print-tree     Print the tree of files that will be downloaded and exists
      --help           Print this help message and exits

    Example:
        download-data.sh --download-path /path/to/download/folder/

    Requirements:
      * curl
    "
    }

    function download_file() {
        local file_url="$1"
        local file_path="$2"
        local file_size="$3"
        local hf_file_size="$4"
        local count_num="$5"
        local dest_file_size

        # Check if the file exists and it is the correct size
        if [[ -f "${file_path}" ]]; then
            local dest_file_size="$(stat --format %s "${file_path}")"
            if [[ "${dest_file_size}" -eq "${file_size}" ]]; then
                echo "File already exists: ${file_path}" 1>&2
                return
            fi
        fi

        # Create the directory if it doesn't exist
        if [[ "${dryrun}" == "false" ]]; then
            mkdir -p "$(dirname "${file_path}")"

            # Download the file
            echo "Downloading ${file_size} bytes (${hf_file_size}) to '${file_path}', ${count_num} / __FILE_COUNT__" 1>&2
            curl --create-dirs --continue-at - --output "${file_path}" --url "${file_url}"
        else
            # Print the mkdir command
            if [[ ! -d "$(dirname "${file_path}")" ]]; then
              echo "mkdir -p $(dirname \"${file_path}\")"
            fi

            # Print the curl command
            echo "curl --create-dirs --continue-at - --output \"${file_path}\" --url \"${file_url}\""
        fi
    }
    
    function print_tree() {
      echo '__PRINT_TREE__'
    }

    # Initialise the arguments
    download_path=""
    dryrun="false"

    # Parse the arguments
    while [ $# -gt 0 ]; do
      case "$1" in
        --download-path)
          download_path="$2"
          shift 1
          ;;
        --dryrun | --dry-run)
          dryrun="true"
          ;;
        -h | --help)
          print_help
          exit 0
          ;;
        --print-tree)
          print_tree
          exit 0
          ;;
      esac
      shift 1
    done

    # Check if download path is set
    if [ -z "$download_path" ]; then
        echo "Error! Download path is required" 1>&2
        print_help
        exit 1
    fi

    # Check if download path exists
    if [ ! -d "$download_path" ]; then
        echo "Error! Download path '${download_path}' does not exist" 1>&2
        exit 1
    fi

    # Provide summary
    echo "Downloading __FILE_COUNT__ files to ${download_path}" 1>&2
    echo "A total of __TOTAL_DATA_SIZE__ ( __HF_DATA_SIZE__ ) will be downloaded to ${download_path}" 1>&2

    # Iterate over each download url and download the file
    """).lstrip("\n").replace(
        "__FILE_COUNT__", str(file_count)
    ).replace(
        "__TOTAL_DATA_SIZE__", str(total_data_size)
    ).replace(
        "__HF_DATA_SIZE__", format_size(total_data_size, binary=True),
    ).replace(
        "__PRINT_TREE__", display_tree
    )


def create_fake_directory(rel_path_list: List[Path]) -> Path:
    root_path = Path(TemporaryDirectory(delete=False).name)

    root_path = root_path / "<DOWNLOAD_PATH>"

    for rel_path in rel_path_list:
        # Create the directory
        (root_path / rel_path).parent.mkdir(parents=True, exist_ok=True)
        # Touch the file
        (root_path / rel_path).touch()

    return root_path


def generate_tree(rel_path_list: List[Path]):
    """
    Generate a tree of downloadss
    :param download_url_dicts:
    :return:
    """

    root_path = create_fake_directory(rel_path_list)

    tree = DisplayTree(
        root_path,
        stringRep=True
    )

    return tree


def get_download_file_template(download_url_dicts: List[Dict[str, str]]):
    # Generate the truee
    script_template = get_script_template(
        file_count=len(download_url_dicts),
        total_data_size=sum(map(
            lambda download_url_dict_iter_: download_url_dict_iter_['fileSizeInBytes'],
            download_url_dicts
        )),
        display_tree=generate_tree(
            list(map(
                lambda donwload_url_dict_iter_: Path(donwload_url_dict_iter_['relativePath']),
                download_url_dicts
            ))
        )
    )

    # Extend the download script with the download commands
    script_template += '\n'.join(
        map(
            lambda download_url_dict_iter_with_index_: " ".join(
                [
                    "download_file",
                    f"\"{download_url_dict_iter_with_index_[1]['presignedUrl']}\"",
                    f"\"{download_url_dict_iter_with_index_[1]['relativePath']}\"",
                    f"\"{download_url_dict_iter_with_index_[1]['fileSizeInBytes']}\"",
                    f"\"{format_size(download_url_dict_iter_with_index_[1]['fileSizeInBytes'], binary=True)}\"",
                    f"\"{(download_url_dict_iter_with_index_[0] + 1)}\"",  # Enumerate
                ]
            ),
            enumerate(download_url_dicts)
        )
    ) + "\n\n"

    script_template += "echo 'Download complete' 1>&2\n"

    return script_template


def handler(event, context):
    """
    Get the packaging job id from the event
    :param event:
    :param context:
    :return:
    """
    packaging_job_id = event['packagingJobId']
    output_uri = event['outputUri']

    # Get the presigned urls
    all_file_objects: List[FileObjectWithPresignedUrlTypeDef] = get_file_objects_with_presigned_urls(
        job_id=packaging_job_id
    )

    download_script = get_download_file_template(
        list(map(
            lambda file_object_iter_: {
                "presignedUrl": file_object_iter_['presignedUrl'],
                "relativePath": file_object_iter_['relativePath'],
                "fileSizeInBytes": file_object_iter_['size'],
            },
            all_file_objects
        ))
    )

    # Upload to s3 bucket
    upload_file(
        file_contents=download_script,
        s3_uri=output_uri
    )


# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['PACKAGING_TABLE_NAME'] = 'data-sharing-packaging-lookup-table'
#     environ['CONTENT_INDEX_NAME'] = 'content-index'
#
#     print(json.dumps(
#         handler(
#             {
#                 "outputUri": "s3://data-sharing-artifacts-472057503814-ap-southeast-2/packages/year=2025/month=04/day=07/pkg.01JR6ZTCE68DY8QC4W7DR2JKZX/final/download-data.tothill-radio-fastq-landing-share.sh",
#                 "packagingJobId": "pkg.01JR6ZTCE68DY8QC4W7DR2JKZX"
#             },
#             None,
#         ),
#         indent=4
#     ))