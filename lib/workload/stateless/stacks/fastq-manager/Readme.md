# Fastq Manager

Welcome to the fastq manager, where here we... well manage fastqs!!

The fastq manager sits over the file manager and provides a way to easily access fastq files and their metadata. 

We provide a few use-cases to consider

1. Given a library to perform an analysis, return the appropriate fastq files for that library.
  * This might be in CWL input format, or a list of file paths, or a list of presigned urls.

2. Given a fastq id, return the metadata associated with that file.
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

We also provide endpoints to run qc, ntsm and file metric calculations on fastq files (like raw md5sum and gzip file size in bytes), which are then 
stored in the database.

We also provide an endpoint to compare two fastq files with ntsm and compare the results. 

## Fastq list row vs fastq set

A fastq list row represents a single fastq pair on a given instrument run id on a given lane. 
No two fastq list rows can have the same instrument run id, lane and index.

A fastq set is a collection of fastq list rows that are all part of the same library.
A fastq set may span multiple lanes and instrument run ids.  

A library may contain multiple fastq sets, but a fastq set can only belong to one library.
A library may contain only one 'current' fastq set.  

A use-case here is a rerun of a library but the original fastq set is still valid.

## API

The swagger API can be found here - https://fastq.dev.umccr.org/schema/swagger-ui

## Events generated

We generate events after any 'PATCH' or 'POST' request to the fastq manager.

These events are sent to the event bus and can be consumed by other services.

Examples of events generated are:

### Fastq Created Events

```json5
{
  "EventBusName": "OrcaBusMain",  // Name of our event bus
  "Source": "orcabus.fastqmanager",  // lowercase name of the service
  "DetailType": "FastqListRowCreated",  // PascalCase name of the event
  "Detail": {
    /* Fastq List Row Response Object */
    "id": "fqr.01JN28R0BMYACXZH2TCRZ80NN8",
    "fastqSetId": "fqs.01JN28R0FE7C9G99ZM4A0F1TRW",
    "index": "GCAAGATC+AGTCGAAG",
    "lane": 2,
    "instrumentRunId": "250123_A00130_0356_BH5GGLDSXF",
    "library": {
      "orcabusId": "lib.01JHJCPB8NRH7T0NZXY1K608ZC",
      "libraryId": "LPRJ250016"
    },
    "platform": "Illumina",
    "center": "UMCCR",
    "date": "2025-01-23T00:00:00",
    "readSet": {
      "r1": {
        "ingestId": "0194dc11-56c3-7d71-900b-1d68d90b9f2d",
        "gzipCompressionSizeInBytes": 28347223381,
        "rawMd5sum": "7ec418fcd0f6026258dbe0c2cadd61b5",  // pragma: allowlist secret
        "s3Uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/ora-compression/250123_A00130_0356_BH5GGLDSXF/20250205d0392e5f/Samples/Lane_2/LPRJ250016/LPRJ250016_S1_L002_R1_001.fastq.ora",
        "storageClass": "Standard",
        "sha256": null
      },
      "r2": {
        "ingestId": "0194dc11-5c5c-77b2-bb10-1c99f85a0785",
        "gzipCompressionSizeInBytes": 28537888181,
        "rawMd5sum": "657daaf985b96683bed2ccfb213c9ad8",  // pragma: allowlist secret
        "s3Uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/ora-compression/250123_A00130_0356_BH5GGLDSXF/20250205d0392e5f/Samples/Lane_2/LPRJ250016/LPRJ250016_S1_L002_R2_001.fastq.ora",
        "storageClass": "Standard",
        "sha256": null
      },
      "compressionFormat": null
    },
    "qc": null,
    "readCount": null,
    "baseCountEst": null,
    "isValid": true,
    "ntsm": null
  }
}
```

Note, that when a fastq set event is created, an event will be created for the set AND for each of the fastq list rows in the set.

### Fastq Update events

These follow the same logic as the fastq created events, but the event name is `FastqListRowUpdated` and the event detail contains the updated fastq list row.

```json5
{
  "EventBusName": "OrcaBusMain",
  "Source": "orcabus.fastqmanager",
  "DetailType": "FastqListRowUpdated",
  "Detail": {
    /* Fastq List Row Response Object */
    // ...
  }
}
```

### Fastq Delete Events

These follow the same logic as the fastq created events, but the event name is `FastqListRowDeleted` and the event detail contains just the id of the fastq list row that was deleted.

```json5
{
  "EventBusName": "OrcaBusMain",
  "Source": "orcabus.fastqmanager",
  "DetailType": "FastqListRowDeleted",
  "Detail": {
    /* Fastq List Row Response Object */
    "id": "fqr.123456789"
  }
}
```


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
      "index": "CTTGTCGA+CGATGTTC.1",
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
  "index": "CTTGTCGA+CGATGTTC.1",
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

You can also query via the index or lane, but you will also need to use the instrument run id when querying via index.


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
  "index": "CTTGTCGA+CGATGTTC.1",
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
  "index": "CTTGTCGA+CGATGTTC",
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