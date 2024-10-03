# Tracking moved objects

The filemanager tracks records from S3 events, which do not describe how objects move from one location to another. Using
S3 events alone, it's not possible to tell whether an object that has been deleted in one place and created in another is
the same object that has been moved, or two different objects. This is because S3 only tracks `Created` or `Deleted`
events.

To track moved objects, the filemanager stores additional information in S3 tags, that gets copied when the object
is moved. This allows the filemanager to track how objects move and also allows it to copy attributes when an object
is moved/copied.

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

Object tags on S3 are limited to 10 tags per object, and each tag can only store 258 unicode characters. The filemanager
avoids storing a large amount of data by using a UUID as the value of the tag, which is linked to object records that
store attributes and data. 

The object tagging process cannot be atomic, so there is a chance for concurrency errors to occur. Tagging can also
fail due to database or network errors. The filemanager only tracks `ingest_id`s if it knows that a tag has been
successfully created on S3, and successfully stored in the database. If tagging fails, or it's not enabled, then the `ingest_id`
column will be null.

The object tagging mechanism also doesn't differentiate between moved objects and copied objects with the same tags.
If an object is copied with tags, the `ingest_id` will also be copied and the above logic will apply.

## Alternative designs

Alternatively, S3 object metadata could also be used to track moves using a similar mechanism. However, metadata can
only be updated by deleting and recreated the object. This process would be much more costly so tagging was chosen instead.
Another approach is to compare object checksums or etags. However, this would also be limited if the checksum is not present,
or  if the etag was computed using a different part-size. Both these approaches could be used in addition to object tagging
to provide more ways to track moves.
