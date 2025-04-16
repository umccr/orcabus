# Fastq Sync Service

The fastq sync service is a simple service that allows step functions with fastq set ids as inputs to 'hang' 
until the requirements of the fastq set have been met. 

This is useful for workflow-glue services that have fastq set ids but need to wait for either

1. The fastq set readsets to be created
2. The fastq set to have been qc'd AND have a fingerprint file and compression information
3. This is also useful for data sharing services that require the fastqs to be unarchived before they can be shared

The step function will then hang at that step until the task token has been 'unlocked' by the fastq sync service.

## Registering task tokens

Workflow glue services can use the fastq sync service by generating the following event

```json5
{
  "EventBusName": "OrcaBusMain",
  "Source": "doesnt matter",
  "DetailType": "FastqSync",
  "Detail": {
    "taskToken":  "uuid",
    "fastqSetId": "fqs.123456",
    // Then one or more of the following
    // Requirements can be left out if not needed
    "requirements": {
      // Do all fastq list rows in the set contain readsets?
      "hasActiveReadSet": true,  
      // Do all fastq list rows in the set contain an ntsm uri?
      "hasFingerprint": true,  
      // Do all fastq list rows in the set contain compression information?
      // Useful if the fastq list rows are in ora format. 
      // Some pipelines require the gzip file size in bytes in order 
      // to stream the gzip file from ora back into s3 
      "hasFileCompressionInformation": true,  
      // Do all fastq list rows in the set contain qc information?
      // We don't use this for anything yet but we may use this in the future
      // to ensure that a fastq set has met the ideal coverage levels
      "hasQc": true,
    },
    "forceUnarchiving": true,  // Force unarchiving of a fastq file if necessary, will fail if not set and fastq is in archive
  }
}
```

The fastq sync service will also trigger the qc, fingerprint or compression information services if they do not exist. 

If any of the fastq list rows are in archive, the fastq sync service will also trigger the fastq unarchiving service to thaw out these fastq list rows.
And place them into the 'byob' bucket.  


## Unlocking task tokens

The fastq sync service will then also listen for the following event types:

1. FastqListRowUpdated (from the fastq management service)
2. UnarchivingJobUpdated (from the fastq unarchiving service, where the status is 'SUCCEEDED')

Everytime one of the events is triggered, the fastq sync service will check if the fastq list row or fastq set has met the requirements.
If all requirements are met for the fastq set, the fastq sync service will unlock the task token.
