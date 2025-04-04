#!/usr/bin/env bash

# Set to fail
set -euo pipefail

# Set python3 version
hash -p /usr/bin/python3.12 python3

# Functions
echo_stderr(){
  echo "$(date -Iseconds): $1" 1>&2
}

get_gz_filesize(){
  local aws_s3_path="${1}"
  aws s3 cp \
    "${aws_s3_path}" \
    - | \
  wc -c
}

get_ora_filesize_as_gz(){
  local aws_s3_path="${1}"
  aws s3 cp \
    "${aws_s3_path}" \
    - | \
  orad \
    --gz \
    --gz-level 1 \
    --stdout \
    --ora-reference "${ORADATA_PATH}" \
    - | \
  wc -c
}

# ENVIRONMENT VARIABLES
# Inputs
if [[ ! -v READ_INPUT_URI ]]; then
  echo_stderr "Error! Expected env var 'READ_INPUT_URI' but was not found" 1>&2
  exit 1
fi

# Ensure we have an output uri
if [[ ! -v OUTPUT_URI ]]; then
  echo_stderr "Error! Expected env var 'OUTPUT_URI' but was not found" 1>&2
  exit 1
fi

# Check if R1_INPUT_URI endswith .ora, #
# if so,
# ensure that orad is in PATH and ORADATA_PATH is in the environment
if [[ "${READ_INPUT_URI}" == *.ora ]]; then
  if ! command -v orad &> /dev/null; then
    echo_stderr "Error! Expected 'orad' to be in PATH but was not found" 1>&2
    exit 1
  fi

  if [[ ! -v ORADATA_PATH ]]; then
    echo_stderr "Error! Expected env var 'ORADATA_PATH' but was not found" 1>&2
    exit 1
  fi
fi

# Download the file and pipe through orad with --gz and --gz-level=1 parametres,
# Otherwise just use the standard aws s3 cp
# Then pipe through wc -c to get the file size
if [[ "${READ_INPUT_URI}" == *.ora ]]; then
  file_size="$( \
    get_ora_filesize_as_gz \
      "${READ_INPUT_URI}" \
  )"
else
  file_size="$( \
    get_gz_filesize \
      "${READ_INPUT_URI}" \
  )"
fi

# Write the file size to the output uri
aws s3 cp \
  - \
  "${OUTPUT_URI}" \
<<< "${file_size}"


