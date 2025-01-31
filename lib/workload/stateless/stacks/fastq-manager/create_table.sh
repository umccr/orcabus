#!/usr/bin/env bash

set -euo pipefail

# Check if table exists
if aws dynamodb describe-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --table-name "${TABLE_NAME}" &> /dev/null; then
  echo "Table ${TABLE_NAME} already exists" 1>&2
  exit 0
fi

# Create table
aws dynamodb create-table \
  --profile "${AWS_PROFILE}" \
  --endpoint-url "${AWS_ENDPOINT_URL}" \
  --no-cli-pager \
  --output json \
  --billing-mode PAY_PER_REQUEST \
  --table-name "${TABLE_NAME}" \
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
          "AttributeName": "is_valid",
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
              "is_valid"
            ]
          }
        }
      ]
    '