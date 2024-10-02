# Tracking moved objects

The filemanager tracks records from S3 events, which do not describe how objects move from one location to another. Using
S3 events alone, it's impossible to tell whether an object that has been deleted in one place and created in another is
the same object that has been moved, or two different objects. This is because S3 only tracks `Created` or `Deleted`
events.

To track moved objects, the filemanager has to store additional information on objects, that gets copied when the object
is moved. The design involves using object tagging to store an identifier on all objects that is copied when the 
object is moved. This id can be used to track how object moves.

When records are ingested, the filemanager first checks if the object contains the tag with the id field. If the tag is
present, then the object has been moved, and the new record reuses that id. If not, a new id is generated  and the object
is tagged with it. Later, the database can be queried to find all record matching the id. This represents a sequence of moved
objects.

## Tagging process

The process of tagging is:

* When an object record is ingested, the filemanager queries `Created` events for tags. 
* If the tags can be retrieved, the filemanager looks for a tag called `filemanager_id`. The key name can be 
  configured in the environment variable `FILEMANAGER_INGESTER_TAG_NAME`.
* The tag is parsed as a UUID, and stored in the `move_id` column of `s3_object` for that record.
* If the tag does not exist, then a new UUID is generated, and the object is tagged on S3 by calling `PutObjectTagging`. 
  The new tag is also stored in the `move_id` column.
* The database is also queried for any records with the same `move_id` so that attributes can be copied to the new record.

This logic is enabled by default, but it can be switched off by setting `FILEMANAGER_INGESTER_TRACK_MOVES`. The filemanager
API provides a way to query the database for records with a given `move_id`.

## Design considerations

Object tags on S3 are limited to 10 tags per object, where each tag can only store 258 unicode characters. This means that it
is not possible a large amount of data or attributes in tags. Instead, filemanager stores a single UUID in the tag, which is
linked to object records that store the attributes and data. 

The object tagging process cannot be atomic, so there is a chance for concurrency errors to occur. Tagging can also
fail due to database or network errors. The filemanager only tracks `move_id`s if it knows that a tag has been
successfully created on S3, and successfully stored in the database. If tagging fails, or it's not enabled then the `move_id`
column will be null.

## Alternative designs

Alternatively, S3 object metadata could also be used to track moves using a similar mechanism. However, metadata can
only be updated by deleting and recreated the object, so tagging was chosen instead. Another mechanism which could track
moved objects is to compare object checksums or etags. This works but may also be limited if checksum is not present, or
if the etag was computed using a different part-size. Both these approaches could be used in addition to object tagging
to provide the filemanager more ways to track moves.
