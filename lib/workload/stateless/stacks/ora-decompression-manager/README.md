# ORA Decompression Manager

Standalone decompression manager, useful for ad-hoc decompression of ora files
without needing to integrate the ora-decompression component.  

You will need to know the estimated file size of the gzipped compressed file.

Takes in a decompression request event and outputs the data in the expected output uri.

```json5
{
  "detailType": "OraFastqListRowDecompression",
  "detail": {
    "status": "READY",
    "payload": {
      "data": {
        "read1OraFileUri": "s3://path/to/read1OraFileUri.ora",
        "read1GzOutputFileUri": "s3://path/to/read1GzFileUri.gz",
        "read2OraFileUri": "s3://path/to/read2OraFileUri.ora",
        "read2GzOutputFileUri": "s3://path/to/read2GzFileUri.gz",
        "read1EstimatedGzFileSize": "123456789",  // In Bytes
        "read2EstimatedGzFileSize": "123456789",  // In Bytes
      }
    }
  }
}
```

Which then relays the following event once complete

```json5
{
  "detailType": "OraFastqListRowDecompression",
  "detail": {
    "status": "COMPLETE",
    "payload": {
      "data": {
        "read1OraFileUri": "s3://path/to/read1OraFileUri.ora",
        "read1GzOutputFileUri": "s3://path/to/read1GzFileUri.gz",
        "read2OraFileUri": "s3://path/to/read2OraFileUri.ora",
        "read2GzOutputFileUri": "s3://path/to/read2GzFileUri.gz",
        "read1EstimatedGzFileSize": "123456789",  // In Bytes
        "read2EstimatedGzFileSize": "123456789",  // In Bytes
      }
    }
  }
}
```
