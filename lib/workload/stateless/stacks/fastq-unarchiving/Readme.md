# Fastq Unarchiving service

Given a list of fastq ids, extract the fastq files from archive and return to the restore directory.

The unarchiving service uses a REST API endpoint to create and query extraction jobs. 

Events are raised once a job completes.  

The jobs use the s3-steps-copy and run 'per instrument run id'.  

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
      "fqs.12345"
    ]
  }   
}
```

Since the files will have updated ingest ids that match the original, a user can query the fastq ids to find the new s3 uris.  

We also allow users to use a fastq list row id to find the available job.


