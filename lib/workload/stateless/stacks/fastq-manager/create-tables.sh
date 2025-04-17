#!/usr/bin/env bash

set -euo pipefail

# Check if table exists
if aws dynamodb describe-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --table-name "${FQLR_TABLE_NAME}" &> /dev/null; then
  echo "Table ${FQLR_TABLE_NAME} already exists" 1>&2
  exit 0
fi

# Create fastq list row table
aws dynamodb create-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --no-cli-pager \
  --output json \
  --billing-mode PAY_PER_REQUEST \
  --table-name "${FQLR_TABLE_NAME}" \
  --key-schema \
    '
      [
        {
          "AttributeName": "id",
          "KeyType":"HASH"
        }
      ]
    ' \
  --attribute-definitions \
    '
      [
        {
          "AttributeName": "id",
          "AttributeType": "S"
        },
        {
          "AttributeName": "rgid_ext",
          "AttributeType": "S"
        },
        {
          "AttributeName": "library_orcabus_id",
          "AttributeType": "S"
        },
        {
          "AttributeName": "instrument_run_id",
          "AttributeType": "S"
        },
        {
          "AttributeName": "fastq_set_id",
          "AttributeType": "S"
        }
      ]
    ' \
  --global-secondary-indexes \
    '
      [
        {
          "IndexName": "rgid_ext-index",
          "KeySchema": [
            {
              "AttributeName": "rgid_ext",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "library_orcabus_id",
              "instrument_run_id",
              "fastq_set_id",
              "is_valid"
            ]
          }
        },
        {
          "IndexName": "library_orcabus_id-index",
          "KeySchema": [
            {
              "AttributeName": "library_orcabus_id",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "rgid_ext",
              "instrument_run_id",
              "fastq_set_id",
              "is_valid"
            ]
          }
        },
        {
          "IndexName": "instrument_run_id-index",
          "KeySchema": [
            {
              "AttributeName": "instrument_run_id",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "rgid_ext",
              "library_orcabus_id",
              "fastq_set_id",
              "is_valid",
              "index",
              "lane"
            ]
          }
        },
        {
          "IndexName": "fastq_set_id-index",
          "KeySchema": [
            {
              "AttributeName": "fastq_set_id",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "rgid_ext",
              "library_orcabus_id",
              "instrument_run_id",
              "is_valid"
            ]
          }
        }
      ]
    '

# Check if table exists
if aws dynamodb describe-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --table-name "${FQS_TABLE_NAME}" &> /dev/null; then
  echo "Table ${FQS_TABLE_NAME} already exists" 1>&2
  exit 0
fi

# Create fastq set table
aws dynamodb create-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --no-cli-pager \
  --output json \
  --billing-mode PAY_PER_REQUEST \
  --table-name "${FQS_TABLE_NAME}" \
  --key-schema \
    '
      [
        {
          "AttributeName": "id",
          "KeyType":"HASH"
        }
      ]
    ' \
  --attribute-definitions \
    '
      [
        {
          "AttributeName": "id",
          "AttributeType": "S"
        },
        {
          "AttributeName": "library_orcabus_id",
          "AttributeType": "S"
        }
      ]
    ' \
  --global-secondary-indexes \
    '
      [
        {
          "IndexName": "library_orcabus_id-index",
          "KeySchema": [
            {
              "AttributeName": "library_orcabus_id",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "is_current_fastq_set",
              "allow_additional_fastq"
            ]
          }
        }
      ]
    '


# Create fastq job table
if aws dynamodb describe-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --table-name "${FASTQ_JOB_TABLE_NAME}" &> /dev/null; then
  echo "Table ${FASTQ_JOB_TABLE_NAME} already exists" 1>&2
  exit 0
fi

# Create fastq set table
aws dynamodb create-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --no-cli-pager \
  --output json \
  --billing-mode PAY_PER_REQUEST \
  --table-name "${FASTQ_JOB_TABLE_NAME}" \
  --key-schema \
    '
      [
        {
          "AttributeName": "id",
          "KeyType":"HASH"
        }
      ]
    ' \
  --attribute-definitions \
    '
      [
        {
          "AttributeName": "id",
          "AttributeType": "S"
        },
        {
          "AttributeName": "fastq_id",
          "AttributeType": "S"
        },
        {
          "AttributeName": "job_type",
          "AttributeType": "S"
        },
        {
          "AttributeName": "status",
          "AttributeType": "S"
        }
      ]
    ' \
  --global-secondary-indexes \
    '
      [
        {
          "IndexName": "fastq_id-index",
          "KeySchema": [
            {
              "AttributeName": "fastq_id",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "job_type",
              "status"
            ]
          }
        },
        {
          "IndexName": "job_type-index",
          "KeySchema": [
            {
              "AttributeName": "job_type",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "fastq_id",
              "status"
            ]
          }
        },
        {
          "IndexName": "status-index",
          "KeySchema": [
            {
              "AttributeName": "status",
              "KeyType": "HASH"
            },
            {
              "AttributeName": "id",
              "KeyType": "RANGE"
            }
          ],
          "Projection": {
            "ProjectionType": "INCLUDE",
            "NonKeyAttributes": [
              "fastq_id",
              "job_type"
            ]
          }
        }
      ]
    '