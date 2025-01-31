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
AWS_PROFILE='local' \
AWS_ENDPOINT_URL='http://localhost:8456' \
bash create_table.sh
```

Generating a POST request locally

```
curl \
  --silent --show-error --fail-with-body --location --request POST \
  --header "Content-Type: application/json" \
  --data '
    {
      "rgid": "CTTGTCGA+CGATGTTC.1",
      "index": "CTTGTCGA",
      "index2": "CGATGTTC",
      "lane": 1,
      "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
      "readSet": {
        "r1": {
          "s3IngestId": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
        },
        "r2": {
          "s3IngestId": "0193cdc0-4c7a-7e23-8d4d-00561ae2ca59"
        }
      },
      "isValid": true,
      "library": {
        "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
        "libraryId": "LPRJ240775"
      }
    }
  ' \
  --url "http://127.0.0.1:8001/api/v1/fastq" | \
jq
```

Gives 

```json
{
  "id": "fqr.01JJ3RASC32XCMPG9S77FGVY11",
  "rgid": "CTTGTCGA+CGATGTTC.1",
  "index": "CTTGTCGA",
  "index2": "CGATGTTC",
  "lane": 1,
  "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
  "library": {
    "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
    "libraryId": "LPRJ240775"
  },
  "readSet": {
    "compressionFormat": null,
    "r1": {
      "s3IngestId": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
    },
    "r2": {
      "s3IngestId": "0193cdc0-4c7a-7e23-8d4d-00561ae2ca59"
    }
  },
  "qc": {
    "insertSizeEstimate": "20",
    "rawWgsCoverageEstimate": "25",
    "r1Q20Fraction": "0.99",
    "r2Q20Fraction": "0.98",
    "r1GcFraction": "0.54",
    "r2GcFraction": "0.5"
  },
  "readCount": null,
  "baseCountEst": null,
  "isValid": false,
  "ntsm": null
}
```

## Listing Fastq Files

By default only valid fastq files are returned. To return all fastq files, set the `valid` query parameter to `ALL`.

```
curl \
  --silent \
  --fail-with-body \
  --location \
  --header "Authorization: Bearer ${ORCABUS_TOKEN}" \
  --url "https://fastq.dev.umccr.org/api/v1/fastq?valid=ALL" 
```

You can query via the instrument run id, or library id (either orcabus id or library id are appropriate).  

You can also query via the rgid, but you will also need to use the instrument run id when querying via rgid.


## Validate a fastq pair

To validate a fastq pair, you can use the following curl command:

```shell
curl \
  --request PATCH --silent \
  --fail-with-body \
  --location \
  --url "http://127.0.0.1:8001/api/v1/fastq/fqr.01JJ3RASC32XCMPG9S77FGVY11/validate" | \
jq
```

Note that the `fqr.` prefix is optional

One can also do 

```shell
curl \
  --request PATCH --silent \
  --fail-with-body \
  --location \
  --url "http://127.0.0.1:8001/api/v1/fastq/01JJ3RASC32XCMPG9S77FGVY11/validate" | \
jq
```

Gives

```json
{
  "id": "fqr.01JJ3RASC32XCMPG9S77FGVY11",
  "rgid": "CTTGTCGA+CGATGTTC.1",
  "index": "CTTGTCGA",
  "index2": "CGATGTTC",
  "lane": 1,
  "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
  "library": {
    "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
    "libraryId": "LPRJ240775"
  },
  "readSet": {
    "compressionFormat": null,
    "r1GzipCompressionSizeInBytes": null,
    "r2GzipCompressionSizeInBytes": null,
    "r1": {
      "s3IngestId": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
    },
    "r2": {
      "s3IngestId": "0193cdc0-4c7a-7e23-8d4d-00561ae2ca59"
    }
  },
  "qc": null,
  "readCount": null,
  "baseCountEst": null,
  "isValid": true,
  "ntsm": null
}
```

## Adding qc stats to a fastq pair

To add qc stats to a fastq pair, you can use the following curl command:

```shell
curl \
  --request PATCH \
  --silent \
  --fail-with-body \
  --location \
  --data '
    {
      "insertSizeEstimate": 20, 
      "rawWgsCoverageEstimate": 25, 
      "r1Q20Fraction": 0.99, 
      "r2Q20Fraction": 0.98, 
      "r1GcFraction": 0.54, 
      "r2GcFraction": 0.50
    }
  ' \
  --url "http://127.0.0.1:8001/api/v1/fastq/fqr.01JJ3RASC32XCMPG9S77FGVY11/addQcStats" | \
jq  
```

Yields

```json
{
  "id": "fqr.01JJ3RASC32XCMPG9S77FGVY11",
  "rgid": "CTTGTCGA+CGATGTTC.1",
  "index": "CTTGTCGA",
  "index2": "CGATGTTC",
  "lane": 1,
  "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
  "library": {
    "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
    "libraryId": "LPRJ240775"
  },
  "readSet": {
    "compressionFormat": null,
    "r1GzipCompressionSizeInBytes": null,
    "r2GzipCompressionSizeInBytes": null,
    "r1": {
      "s3IngestId": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
    },
    "r2": {
      "s3IngestId": "0193cdc0-4c7a-7e23-8d4d-00561ae2ca59"
    }
  },
  "qc": {
    "insertSizeEstimate": 20,
    "rawWgsCoverageEstimate": 25,
    "r1Q20Fraction": 0.99,
    "r2Q20Fraction": 0.98,
    "r1GcFraction": 0.54,
    "r2GcFraction": 0.5
  },
  "readCount": null,
  "baseCountEst": null,
  "isValid": false,
  "ntsm": null
}
```

Note that snake case for inputs is also supported, so the following is also valid:

```shell
curl \
  --request PATCH \
  --silent \
  --fail-with-body \
  --location \
  --data '
    {
      "insertSizeEstimate": 20, 
      "rawWgsCoverageEstimate": 25, 
      "r1Q20Fraction": 0.99, 
      "r2Q20Fraction": 0.98, 
      "r1GcFraction": 0.54, 
      "r2GcFraction": 0.50
    }
  ' \
  --url "http://127.0.0.1:8001/api/v1/fastq/fqr.01JJ3RASC32XCMPG9S77FGVY11/addQcStats" | \
jq
```

## Adding read count to a fastq pair

```bash
curl \
  --silent \
  --fail-with-body \
  --location \
  --request PATCH \
  --header "Authorization: Bearer ${ORCABUS_TOKEN}" \
  --data '
    {
      "readCount": 12345,
      "baseCountEst": 12345000
    }
  ' \
  --url "https://fastq.dev.umccr.org/api/v1/fastq/fqr.01JJ37C4KA6THTP0XVQDSSJKJQ/addReadCount" | \
jq
```

## Add information regarding the compression format and gzip size

```bash
curl \
  --silent \
  --fail-with-body \
  --location \
  --request PATCH \
  --header "Authorization: Bearer ${ORCABUS_TOKEN}" \
  --data '
    {
      "compressionFormat": "ORA",
      "r1GzipCompressionSizeInBytes": 12345000,
      "r2GzipCompressionSizeInBytes": 12345999
    }
  ' \
  --url "https://fastq.dev.umccr.org/api/v1/fastq/fqr.01JJ37C4KA6THTP0XVQDSSJKJQ/addFileCompressionInformation" | \
jq
```

## Add information regarding the ntsm uri

```bash
curl \
  --silent \
  --fail-with-body \
  --location \
  --request PATCH \
  --header "Authorization: Bearer ${ORCABUS_TOKEN}" \
  --data '
    {
      "ntsm": "s3://path/to/ntsm-file.bin"
    }
  ' \
  --url "https://fastq.dev.umccr.org/api/v1/fastq/fqr.01JJ37C4KA6THTP0XVQDSSJKJQ/addFileCompressionInformation" | \
jq
```