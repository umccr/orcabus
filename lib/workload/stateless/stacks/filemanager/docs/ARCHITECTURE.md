# Filemanager

The aim of the filemanager is to maintain a database state that is as correct as possible at the time an event is received.
Broadly, the architecture of filemanager reflects this, where cloud storage events that contain information about objects
are processed and stored in the database. The database tables reflect the information from the events, and data is stored
in the `s3_object` tables.

Some details about S3 event processing needs to be addressed in filemanager, specifically in relation to out of order
and duplicate events.

## Event ingestion

The filemanager determines the location of objects in cloud storage by ingesting events like the [AWS S3 events][s3-events].
However, events for most cloud services only guarantee that events are received at least once. Duplicate events may be received
or events could be received out of order, and the filemanager should handle this. This needs to occur both in application
code and at the database level because events can be out of order across Lambda function calls.

To detect out of order and duplicate events, the filemanager relies on the fields within the events received from AWS.
These fields are the `bucket`, `key`, `version_id`, and `sequencer` values. For an S3 object, when the `bucket`, `key`
and `version_id` are the same, the sequencer value determines the ordering of events. An event occurs earlier if it's
sequencer value is smaller than another event's sequencer value. Duplicate events have the same `bucket`, `key`,
`version_id` and `sequencer` values for an event type.

Objects can also be ingested using an external [S3 inventory][s3-inventory]. The S3 inventory does not contain any 
sequencer values, and so it cannot be compared directly with events containing sequencer values. The filemanager makes
some assumptions about how to ingest S3 inventory data as there is inherent ambiguity in the ordering of data.
See the [implementation section][inventory-implementation] of `filemanager-inventory-lambda` for more information.

### Duplicate events

Within the application code, duplicate events are removed in the [events] module by matching on the `bucket`, `key`,
`version_id` and `sequencer` values.

At the database level, duplicate events are removed using a unique constraint on the same values and an
`on conflict on constraint` statement.

### Out of order events

Within the application code, out of order events are removed within the [events] module by comparing sequencer values.

By default, filemanager makes no assumption about the ordering of events, and ingests events in the order that they arrive.
The sequencer value is stored on the `s3_object` table, which allows ordering entries when querying.

#### Paired ingest mode
Ordering events on ingestion can be turned on by setting `PAIRED_INGEST_MODE=true` as an environment variable. This has
a performance cost on ingestion, but it removes the requirment to order events when querying the database.

At the database level, events are processed as they arrive. For each object in the database, the sequencer value is
recorded. When an event is inserted, it is first checked to see if it belongs to an already existing object, i.e. whether
there are any objects with sequencer values that are greater (for created events) or lower (for deleted events) than the
existing sequencer. If this condition is met, then the existing object is updated, and the old event is returned by the
database to be re-inserted. If it is not met, then the event is inserted normally.

[events]: ../filemanager/src/events
[s3-events]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html
[s3-inventory]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
[inventory-implementation]: ../filemanager-inventory-lambda/README.md#implementation