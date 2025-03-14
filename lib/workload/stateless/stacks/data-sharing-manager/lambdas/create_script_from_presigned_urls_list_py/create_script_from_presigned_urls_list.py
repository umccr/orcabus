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

from pathlib import Path
from textwrap import dedent
from typing import List, Dict
from directory_tree import DisplayTree
from tempfile import TemporaryDirectory
from humanfriendly import format_size

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
        local hf_file_size="$3"
        local count_num="$4"
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
            echo "Downloading ${file_size} bytes (${hf_file_size}) to '${file_path}', ${count_num} / __COUNT__" 1>&2
            curl --create-dirs --continue-at - --output "${file_path}" --url "${file_url}"
        else
            # Print the mkdir command
            if [[ ! -d "$(dirname "${file_path}")" ]]; then
              echo "mkdir -p \"$(dirname \"${file_path}\")\""
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

    tree = DisplayTree(root_path)

    return tree


def get_download_file_template(download_url_dicts: List[Dict[str, str]]):
    script_template = get_script_template(
        file_count=len(download_url_dicts),
        total_data_size=sum(map(
            lambda download_url_dict_iter_: download_url_dict_iter_['fileSizeInBytes'],
            download_url_dicts
        ))
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
                    f"\"{download_url_dict_iter_with_index_[0]}",  # Enumerate
                ]
            ),
            enumerate(download_url_dicts)
        )
    ) + "\n\n"

    script_template += "echo 'Download complete' 1>&2\n"
