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

### Current vs historical records

Since the filemanager database keeps growing as records are never deleted, the current state of records is stored on a
`is_current_state` column. This column indicates which records represent real objects in S3, and which records are
historical data that represent previously deleted objects.

This value is computed when events are ingested, and automatically kept up to date. This is done at ingestion because
the performance impact of determining this is too great on every API call. This does incur a performance penalty for
ingestion. However, it should be minimal as only other current records need to be considered. This is because records
only need to transition from current to historical (and not the other way around).

For example, consider a `Created` event `"A"` for a given key. `"A"` starts with `is_current_state` set to true.
Then, another `Created` event `"B"` comes in for the same key, which represents overwriting that object. Now, `"B"`
has `is_current_state` set to true. The ingester needs to flip `is_current_state` to false on `"A"` as it's no longer current.
This also applies if a new version of an object is created.

Since records which are current represent a smaller subset of all records, only a smaller part of the database needs to be
queried to do this logic. This is currently performant enough to happen at ingestion, however if it becomes an issue,
it could be performed asynchronously in a different process.

#### Paired ingest mode

Ordering events on ingestion can be turned on by setting `PAIRED_INGEST_MODE=true` as an environment variable. This has
a performance cost on ingestion, but it removes the requirment to order events when querying the database.

At the database level, events are processed as they arrive. For each object in the database, the sequencer value is
recorded. When an event is inserted, it is first checked to see if it belongs to an already existing object, i.e. whether
there are any objects with sequencer values that are greater (for created events) or lower (for deleted events) than the
existing sequencer. If this condition is met, then the existing object is updated, and the old event is returned by the
database to be re-inserted. If it is not met, then the event is inserted normally.

#### Null sequencer events

Some event types do not contain a sequencer value, such as lifecycle transition events. Null sequencer values are also
generated by the crawl and inventory ingest processes. To handle these events, the filemanager labels events as either
`Created` or `Deleted`, and then generates a sequencer value. The generated sequencer value only holds a comparison to
other generated sequencers on the same bucket, key and version_id, based on the event time, and does not intefere with
the ordering and ingestion of AWS-native sequencer values.

To do this, the filemanager gets a records from the database with `is_current_state` set to true, and then appends an
incrementing number to the end of the existing sequencer. For example, a sequencer of `0055AED6DCD90281E4` in the database
gets padded and an u64 is appended to the end:

`0055AED6DCD90281E4000000000000-0100000000000000`

If another event with a null sequencer comes in, the number gets incremented:

`0055AED6DCD90281E4000000000000-0200000000000000`

When an AWS-native sequencer comes in, it will be ordered as greater than the generated sequencer:

`0055AED6DCD90281E5`

If the database did not contain a record for the current state of the object, then the lowest possible "0" sequencer
is used:

`000000000000000000000000000000-0100000000000000`

The padding is necessary because AWS doesn't guarantee that the sequencer value is the same length, so a maximum
supported sequencer padding is used to ensure correct ordering. If an event comes in that has a longer sequencer, the
ingestion fails. In practice, the padding is set large enough so that it will never be exceeded.

`PAIRED_INGEST_MODE` does not support S3 events like lifecycle transitions because they do not represent true `Created`
events.

[events]: ../filemanager/src/events
[s3-events]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html
[s3-inventory]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
[inventory-implementation]: ../filemanager-inventory-lambda/README.md#implementation
