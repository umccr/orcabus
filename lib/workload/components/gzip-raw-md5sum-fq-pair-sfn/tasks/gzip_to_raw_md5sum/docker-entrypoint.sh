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

# Ensure we have an output uri
if [[ ! -v OUTPUT_URI ]]; then
  echo "$(date -Iseconds): Error! Expected env var 'OUTPUT_URI' but was not found" 1>&2
  exit 1
fi

# ICAV2 ENV VARS
export ICAV2_BASE_URL="https://ica.illumina.com/ica/rest"

# SECRET KEY FOR ICAV2
if [[ ! -v ICAV2_ACCESS_TOKEN_SECRET_ID ]]; then
  echo "$(date -Iseconds): Error! Expected env var 'ICAV2_ACCESS_TOKEN_SECRET_ID' but was not found" 1>&2
  exit 1
fi

# Get the ICAV2 access token
echo "$(date -Iseconds): Collecting the ICAV2 access token" 1>&2
ICAV2_ACCESS_TOKEN="$( \
  aws secretsmanager get-secret-value \
    --secret-id "${ICAV2_ACCESS_TOKEN_SECRET_ID}" \
    --output text \
    --query SecretString
)"
export ICAV2_ACCESS_TOKEN

# Set AWS credentials access for aws s3 cp
echo "$(date -Iseconds): Collecting the AWS S3 Access credentials" 1>&2
aws_s3_access_creds_json_str="$( \
  python3 scripts/get_aws_credentials_access.py \
    "$(dirname "${OUTPUT_URI}")/"
)"

# Set the estimated file size
echo "$(date -Iseconds): Setting estimated file size to 33" 1>&2
ESTIMATED_FILE_SIZE="33"  # 32 bytes in a md5sum (33 when you include the newline)

# Download the file and pipe through orad
# to validate the checksum
# Because we use --status on md5sum, we will
# get a non-zero exit code if the checksum fails
echo "$(date -Iseconds): Starting md5sum process" 1>&2
wget \
  --quiet \
  --output-document - \
  "$(  \
    python3 scripts/get_icav2_download_url.py \
    "${INPUT_URI}"
  )" | \
unpigz \
 --stdout | \
md5sum | \
sed 's/  -//g' | \
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
    --expected-size="${ESTIMATED_FILE_SIZE}" \
    --sse=AES256 \
    - \
    "$( \
      python3 scripts/get_s3_uri.py \
        "$(dirname "${OUTPUT_URI}")/" \
    )$( \
      basename "${OUTPUT_URI}" \
    )"
)
echo "$(date -Iseconds): md5sum calculation complete" 1>&2
