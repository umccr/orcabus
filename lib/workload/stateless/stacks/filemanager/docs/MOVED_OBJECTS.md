# Tracking moved objects

The filemanager tracks records from S3 events, which do not describe how objects move from one location to another. Using
S3 events alone, it's not possible to tell whether an object that has been deleted in one place and created in another is
the same object that has been moved, or two different objects. This is because S3 only tracks `Created` or `Deleted`
events.

To track moved objects, filemanager stores additional information in S3 tags. The tag gets updated when the object
is moved. This allows the filemanager to track how objects move and also allows it to copy attributes when an object
is moved/copied. This process is described [below](#tagging-process).

## Tagging process

The process of tagging is:

* When an object record is ingested, the filemanager queries `Created` events for tags. 
* If the tags can be retrieved, the filemanager looks for a key called `ingest_id`. The key name can be 
  configured in the environment variable `FILEMANAGER_INGESTER_TAG_NAME`.
* The tag is parsed as a UUID, and stored in the `ingest_id` column of `s3_object` for that record.
* If the tag does not exist, then a new UUID is generated, and the object is tagged on S3 by calling `PutObjectTagging`. 
  The new tag is also stored in the `ingest_id` column.
* The database is also queried for any records with the same `ingest_id` so that attributes can be copied to the new record.

This logic is enabled by default, but it can be switched off by setting `FILEMANAGER_INGESTER_TRACK_MOVES`. The filemanager
API provides a way to query the database for records with a given `ingest_id`.

## Design considerations

Object tags on S3 are [limited][s3-tagging] to 10 tags per object, and each tag can only store 258 unicode characters.
The filemanager avoids storing a large amount of data by using a UUID as the value of the tag, which is linked to object
records that store attributes and data. 

The object tagging process cannot be atomic, so there is a chance for concurrency errors to occur. Tagging can also
fail due to database or network errors. The filemanager only tracks `ingest_id`s if it knows that a tag has been
successfully created on S3, and successfully stored in the database. If tagging fails, or it's not enabled, then the `ingest_id`
column will be null.

The act of tagging the object allows it to be tracked - ideally this is done as soon as possible. Currently, this happens
at ingestion, however this could have performance implications. Alternative approaches should consider asynchronous tagging.
For example, [`s3:ObjectTagging:*`][s3-tagging-event] events could be used for this purpose.

The object tagging mechanism also doesn't differentiate between moved objects and copied objects with the same tags.
If an object is copied with tags, the `ingest_id` will also be copied and the above logic will apply.

## Alternative designs

Alternatively, S3 object metadata could also be used to track moves using a similar mechanism. However, metadata can
[only be updated][s3-metadata] by deleting and recreated the object. This process would be much more costly so tagging 
was chosen instead.

Another approach is to compare object checksums or etags. However, this would also be limited if the checksum is not present,
or if the etag was computed using a different part-size. It also fails if the checksum is not expected to be the same,
for example, if tracking set of files that are compressed. Both these approaches could be used in addition to object tagging
to provide more ways to track moves.

[s3-tagging]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-tagging.html
[s3-tagging-event]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html#supported-notification-event-types
[s3-metadata]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html
