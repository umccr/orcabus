# filemanager-inventory-lambda

This crate contains a Lambda function which can ingest events using an [S3 inventory][s3-inventory]. This is useful to
sync up data sources that may not be directly deployed as an [event-source] in orcabus, or to sync old data that existed
before the filemanager was deployed.

## Usage

To use this function, call it with the bucket and key of the inventory `manifest.json` file created by S3 Inventory:
```sh
aws lambda invoke \
  --function-name orcabus-filemanager-inventory \
  --payload '{ "bucket": "inventory_manifest_location", "key": "manifest.json" }' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

The key can also point to the `manifest.checksum` created by S3 Inventory, which assumes that the manifest file
exists under the same key prefix and a `.json` extension.

Alternatively, this function can be called with the [`manifest.json` data][manifest-json] serialized directly into the function input:
```sh
payload='
{
      "sourceBucket": "example-source-bucket",
      "destinationBucket": "arn:aws:s3:::example-inventory-destination-bucket",
      "version": "2016-11-30",
      "creationTimestamp" : "1514944800000",
      "fileFormat": "CSV",
      "fileSchema": "Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner",
      "files": [
          {
              "key": "Inventory/example-source-bucket/2016-11-06T21-32Z/files/939c6d46-85a9-4ba8-87bd-9db705a579ce.csv.gz",
              "size": 2147483647,
              "MD5checksum": "<checksum_value>"
          }
      ]
}
'
aws lambda invoke \
  --function-name orcabus-filemanager-inventory \
  --payload "$payload" \
  --cli-binary-format raw-in-base64-out \
  response.json
```

The `manifest.json` is only required to contain the `destinationBucket`, `fileFormat`, and the `key` component of the `files`.
Note, that the `destionationBucket` specifies the location of the inventory file. It does not need to be a full ARN,
and can instead be the bucket name. The `fileFormat` is not required because for Parquet and Orc, the file schema is
encoded within the inventory data. For CSV, AWS does not include header fields. So if the file schema is missing, parsing
will attempt to use CSV headers if they are present, or default to the following headers if not present:

```"Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, LastModifiedDate, ETag, StorageClass"```

## Implementation

This function is implemented to read the inventory data file and ingest the records into the filemanager database. In order to
do this, it assumes that the inventory data represents the state of the S3 bucket at the time the inventory is ingested.
No checks are performed to determine if this is true. A check could involve calling a `HeadObject` on each key of the
inventory, however this functionality is not currently implemented. It is recommended that the inventory data bucket is 
locked during ingestion to prevent any race conditions.

The filemanager database still attempts to maintain a consistent state, even if additional events occur while ingesting
the inventory. Notably, it creates database records such that any deleted events on an object bind to records created by the
inventory. The ordering of sequencer values is maintained (i.e. created events always occur before deleted events).

### Details

The filemanager converts the inventory records into database records by assigning each inventory record an empty string
sequencer (`SEQUENCER_A`). This means that any deleted event (with `SEQUENCER_B`) that occurs after the record is ingested automatically
binds to the inventory record in the `s3_object` table, as the sequencer value is always greater than the empty string.

After this, the following de-duplication and reordering logic applies:
* Created/deleted events with sequencer values that occur after the deleted event (with `SEQUENCER_A`) make new database records.
* Created events with sequencer values that occur before the deleted event (with `SEQUENCER_A`) bind with this database record. The old inventory
  record (with `SEQUENCER_B`) is not re-processed because it is assumed that the created event occurred before the inventory was created.
* Deleted events with sequencer values that occur before the deleted event (with `SEQUENCER_A`) bind with this database record. The deleted
  event (with `SEQUENCER_A`) is re-processed because it is assumed that it occurred after the inventory was created.

[s3-inventory]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
[event-source]: ../../../../stateful/stacks/shared/constructs/event-source/index.ts
[manifest-json]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory-location.html#storage-inventory-location-manifest