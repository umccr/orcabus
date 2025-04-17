# Fastq Unarchiving service

Given a list of fastq ids (fastq list row orcabus ids), extract the fastq files from archive and return to the restore directory.

The unarchiving service uses a REST API endpoint to create and query extraction jobs. 

Events are raised once a job completes.  

The jobs use the [steps-s3-copy](https://github.com/umccr/steps-s3-copy) and groups 'per instrument run id' to prevent overlapping file names.

## API

The swagger page can be found here - https://fastq-unarchiving.dev.umccr.org/schema/swagger-ui#/

## Event Models

### JobStartedEvent

```json5
{
  "EventBusName": "OrcaBusMain",
  "Source": "fastqunarchiving.manager",
  "DetailType": "UnarchivingStarted",
  "Detail": {
    "jobId": "ulid",
    "status": "RUNNING",
    "createTime": "string",
    "updateTime": "string",
    "fastqIds": [
      "fqr.12345"
    ]
  }   
}
```

### Job Completed Event

```json
{
  "EventBusName": "OrcaBusMain",
  "Source": "fastqunarchiving.manager",
  "DetailType": "UnarchivingCompleted",
  "Detail": {
    "jobId": "ulid",
    "status": "COMPLETED",
    "createTime": "string",
    "updateTime": "string",
    "fastqIds": [
      "fqr.12345"
    ]
  }
}
```

## Additional notes

Since the files will have updated ingest ids that match the original, a user can query the fastq ids to find the new s3 uris.  

We also allow users to use a fastq list row id to find the available job.

Currently the fastq unarchiver will place files in the restore directory. 
Files placed in the restore directory will be deleted after 14 days.

