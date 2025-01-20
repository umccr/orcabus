# Fastq Manager

Welcome to the fastq manager, where we, well manage fastqs!!

The fastq manager sits over the file manager and provides a way to easily access fastq files and their metadata. 

We provide a few use-cases to consider

1. Given a library to perform an analysis, return the appropriate fastq files for that library.\
  * This might be in CWL input format, or a list of file paths, or a list of presigned urls.

2. Given a fastq file, return the metadata associated with that file.
  * This might be 
    * library, 
    * sample name, 
    * instrument run, 
    * lane, 
    * size, 
    * read count
    * the md5sum, 
    * the url, etc.

3. Search for fastq files given a project, subject, instrument run id or other metadata.


## Local Development

Spin up the docker images with 'docker compose up -d', this will create a local dynamodb instance.

You will still need to manually create the table in dynamodb, you can do this by running the following command:

```bash
aws dynamodb create-table \
  --profile local \
  --endpoint-url http://localhost:8000 \
  --billing-mode PAY_PER_REQUEST \
  --table-name fastq_list_row \
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
              "instrument_run_id"
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
              "instrument_run_id"
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
              "library_orcabus_id"
            ]
          }
        }
      ]
    '
```

Generating a POST request locally

```
curl \
  --silent --show-error --fail-with-body --location --request POST \
  --header "Content-Type: application/json" \
  --data '
    {
      "rgid": "abc12348", 
      "instrument_run_id": "270101", 
      "library": {
        "library_id": "l123", 
        "orcabus_id": "lib.ABC"
      }, 
      "files": [
        {
          "s3_uri": "s3://path/to/file", 
          "file_size_in_bytes": "12345678",  
          "s3_object_id": "object-id", 
          "is_archived": "false"
        }
      ]
    }
  ' \
  --url "http://127.0.0.1:8001/v1/fastq" | \
jq
```

Gives 

```json
{
  "id": "fqr.01JHFA4FRGC8XGJJB2SYK5GFMP",
  "rgid": "abc12348",
  "index": null,
  "index2": null,
  "lane": null,
  "instrument_run_id": "270101",
  "library": {
    "orcabus_id": "lib.ABC",
    "library_id": "l123"
  },
  "files": [
    {
      "s3_uri": "s3://path/to/file",
      "file_size_in_bytes": 12345678,
      "s3_object_id": "object-id",
      "is_archived": false
    }
  ],
  "qc": null,
  "read_count": null,
  "base_count_est": null,
  "is_valid": null,
  "is_archived": null,
  "compression_format": null,
  "gzip_compression_size_in_bytes": null,
  "ntsm_uri": null
}
```

## Listing Fastq Files



