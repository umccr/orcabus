# Fastq Sync Service

The fastq sync service is a simple service that allows step functions with task tokens to 'hang' 
until the requirements of either a fastq list row or fastq set have been met. 

This is useful for workflow-glue services that have fastq set ids but need to wait for either

1. The fastq set readsets to be created
2. The fastq set to have been qc'd AND have a fingerprint file and compression information
3. This is also useful for data sharing services that require the fastqs to be unarchived before they can be shared

The step function will then hang at that step until the task token has been 'unlocked'

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
    // Do all fastq list rows in the set contain readsets?
    "hasReadsets": true,  
    // Do all fastq list rows in the set contain an ntsm uri?
    "hasFingerprints": true,  
    // Do all fastq list rows in the set contain compression information?
    // Useful if the fastq list rows are in ora format. 
    // Some pipelines require the gzip file size in bytes in order 
    // to stream the gzip file from ora back into s3 
    "hasCompressionInformation": true,  
    // Do all fastq list rows in the set contain qc information?
    // We don't use this for anything yet but we may use this in the future
    // to ensure that a fastq set has met the ideal coverage levels
    "hasQc": true,
  }
}
```

The fastq sync service will also trigger the qc, fingerprint or compression information services if they do not exist. 

If any of the fastq list rows are in archive, the fastq sync service will also trigger the archive service to unarchive these fastq list rows.

## Unlocking task tokens

The fastq sync service will listen for the following events:

1. FastqListRowUpdated (from the fastq management service)
2. FastqSetUpdated (from the fastq management service)
3. UnarchivingCompleted (from the fastq unarchiving service)

The fastq sync service will then check against the requirements of the fastq set or fastq list row for each task token and if so, unlock the task token.

