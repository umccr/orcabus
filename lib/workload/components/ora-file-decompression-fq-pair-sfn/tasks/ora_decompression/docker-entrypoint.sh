#!/usr/bin/env bash

# Set to fail
set -euo pipefail

# Set python3 version
hash -p /usr/bin/python3.12 python3

# ENVIRONMENT VARIABLES
# Inputs
if [[ ! -v INPUT_URI ]]; then
  echo "$(date -Iseconds): Error! Expected env var 'INPUT_URI' but was not found" 1>&2
  exit 1
fi

if [[ ! -v IS_VALIDATION ]]; then
  IS_VALIDATION="false"
fi

# ICAV2 ENV VARS
export ICAV2_BASE_URL="https://ica.illumina.com/ica/rest"

# SECRET KEY FOR ICAV2
if [[ ! -v ICAV2_ACCESS_TOKEN_SECRET_ID ]]; then
  echo "$(date -Iseconds): Error! Expected env var 'ICAV2_ACCESS_TOKEN_SECRET_ID' but was not found" 1>&2
  exit 1
fi

echo "$(date -Iseconds): Collecting the ICAV2 access token" 1>&2
# Get the ICAV2 access token
ICAV2_ACCESS_TOKEN="$( \
  aws secretsmanager get-secret-value \
    --secret-id "${ICAV2_ACCESS_TOKEN_SECRET_ID}" \
    --output text \
    --query SecretString
)"
export ICAV2_ACCESS_TOKEN

# Download reference
# Section commented out as reference is built-in to the fargate task
# This may change in future if different references are used
#echo "$(date -Iseconds): Downloading the icav2 reference file" 1>&2
#python3 scripts/download_icav2_file.py \
#  "${REFERENCE_URI}" \
#  "oradata-v2.tar.gz"
#tar -xf "oradata-v2.tar.gz"

if [[ "${IS_VALIDATION}" == "true" ]]; then
  # Ensure that the RAW MD5SUM has been provided
  if [[ ! -v RAW_MD5SUM ]]; then
    echo "RAW_MD5SUM is required for validation" 1>&2
    exit 1
  fi

  # Write out the md5sum checksum to a file
  echo "${RAW_MD5SUM}  -" > raw_md5sum.check.txt

  # Download the file and pipe through orad
  # to validate the checksum
  # Because we use --status on md5sum, we will
  # get a non-zero exit code if the checksum fails
  wget \
    --quiet \
    --output-document - \
    "$(  \
      python3 scripts/get_icav2_download_url.py \
      "${INPUT_URI}"
    )" | \
  /usr/local/bin/orad \
    --raw \
    --stdout \
    --ora-reference "${ORADATA_PATH}" \
    - |
  md5sum \
    --check \
    --status \
    raw_md5sum.check.txt

else
  # Ensure we have an output size
  if [[ ! -v OUTPUT_URI ]]; then
  echo "$(date -Iseconds): Error! Expected env var 'OUTPUT_URI' but was not found" 1>&2
  exit 1
  fi

  # Required for aws s3 cp to upload a file from stdin
  if [[ ! -v ESTIMATED_GZ_FILE_SIZE ]]; then
    echo "$(date -Iseconds): Error! Expected env var 'ESTIMATED_GZ_FILE_SIZE' but was not found" 1>&2
    exit 1
  fi

  # If the estimated gz file size is -1, we need to do a double extraction
  # Since we do not have the space to store the gz file and then upload it
  if [[ "${ESTIMATED_GZ_FILE_SIZE}" == "-1" ]]; then
    echo "$(date -Iseconds): Estimated file gz file size is -1, we need to do a double extraction to get the file size" 1>&2
    ESTIMATED_GZ_FILE_SIZE="$( \
      wget \
        --quiet \
        --output-document - \
        "$(  \
          python3 scripts/get_icav2_download_url.py \
          "${INPUT_URI}"
        )" | \
      /usr/local/bin/orad \
        --gz \
        --gz-level 1 \
        --stdout \
        --ora-reference "${ORADATA_PATH}" \
        - | \
      wc -c \
    )"
    echo "$(date -Iseconds): Estimated gz file size is ${ESTIMATED_GZ_FILE_SIZE}" 1>&2
  fi

  # Set AWS credentials access for aws s3 cp
  echo "$(date -Iseconds): Collecting the AWS S3 Access credentials" 1>&2
  aws_s3_access_creds_json_str="$( \
    python3 scripts/get_aws_credentials_access.py \
      "$(dirname "${OUTPUT_URI}")/"
  )"

  # Use a file descriptor to emulate the ora file
  # Write the gzipped ora file to stdout
  echo "$(date -Iseconds): Starting stream and decompression of the ora input file" 1>&2
  # Prefix with qemu-x86_64-static
  # when using the orad x86_64 binary
  # but we have the arm binary
  # qemu-x86_64-static \  # Uncomment this line!
  # When using qemu-x86_64-static, piping through
  # wget may be difficult, and instead may need to use
  # a <() redirection
  wget \
    --quiet \
    --output-document - \
    "$(  \
      python3 scripts/get_icav2_download_url.py \
      "${INPUT_URI}"
    )" | \
  /usr/local/bin/orad \
    --gz \
    --gz-level 1 \
    --stdout \
    --ora-reference "${ORADATA_PATH}" \
    - | \
  (
    AWS_ACCESS_KEY_ID="$( \
      jq -r '.AWS_ACCESS_KEY_ID' <<< "${aws_s3_access_creds_json_str}"
    )" \
    AWS_SECRET_ACCESS_KEY="$( \
      jq -r '.AWS_SECRET_ACCESS_KEY' <<< "${aws_s3_access_creds_json_str}"
    )" \
    AWS_SESSION_TOKEN="$( \
      jq -r '.AWS_SESSION_TOKEN' <<< "${aws_s3_access_creds_json_str}"
    )" \
    AWS_REGION="$( \
      jq -r '.AWS_REGION' <<< "${aws_s3_access_creds_json_str}"
    )" \
    aws s3 cp \
      --expected-size="${ESTIMATED_GZ_FILE_SIZE}" \
      --sse=AES256 \
      - \
      "$( \
        python3 scripts/get_s3_uri.py \
          "$(dirname "${OUTPUT_URI}")/" \
      )$( \
        basename "${OUTPUT_URI}" \
      )"
  )
  echo "$(date -Iseconds): Stream and upload of decompression complete" 1>&2
fi

