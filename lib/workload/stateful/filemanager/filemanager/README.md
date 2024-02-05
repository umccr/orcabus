# filemanager

This crate contains the library code that has functionality for the filemanager. Crates such as [filemanager-ingest-lambda]
and [filemanager-http-lambda] depend on this code to execute filemanager logic.

[filemanager-http-lambda]: ../filemanager-http-lambda
[filemanager-ingest-lambda]: ../filemanager-ingest-lambda

## Project Layout

This crate is divided into modules that handle different parts of the filemanager logic.

* [clients]: Wraps cloud service clients for easier testablity. For example, AWS clients are wrapped
in their own structs and mocked using the [mockall] library, which can be used in tests. In general, this module should only
contain thin wrappers around clients, and any logic should be elsewhere to ensure that the majority of the code remains testable.
* [database]: Provides the connection to the underlying filemanager database and database logic.
* [events]: Converts raw events received from cloud storage into a format accessible by the database. For example, the 
`Collect` trait is used to transform cloud storage events into data usable by the database `Ingest` trait.
* [handlers]: High level code that can be used by other crates to perform filemanager actions.
* [env]: Environment variable handling.
* [error]: Error code associated with filemanager.

Generally code that belongs to a particular cloud service should be put in its own module (e.g. AWS code goes in an `aws` module).

## Event ingestion

The filemanager determines the location of objects in cloud storage by ingesting events like the [AWS S3 events][s3-events].
However, events for most cloud services only guarantee that events are received at least once. Duplicate events may be received
or events could be received out of order, and the filemanager should handle this. This needs to occur both in application
code and at the database level because events can be out of order across Lambda function calls. The aim of the filemanager
is to maintain a database state that is as correct as possible at the time an event is received.

To detect out of order and duplicate events, the filemanager relies on the fields within the events received from AWS.
These fields are the `bucket`, `key`, `version_id`, and `sequencer` values. For an S3 object, when the `bucket`, `key`
and `version_id` are the same, the sequencer value determines the ordering of events. An event occurs earlier if it's
sequencer value is smaller than another event's sequencer value. Duplicate events have the same `bucket`, `key`,
`version_id` and `sequencer` values for an event type.

### Duplicate events

Within the application code, duplicate events are removed in the [events] module by matching on the `bucket`, `key`,
`version_id` and `sequencer` values.

At the database level, duplicate events are removed using a unique constraint on the same values and an
`on conflict on constraint` statement.

### Out of order events

Within the application code, out of order events are removed within the [events] module by comparing sequencer values.

At the database level, events are processed as they arrive. For each object in the database, the sequencer value is
recorded. When an event is inserted, it is first checked to see if it belongs to an already existing object, i.e. whether
there are any objects with sequencer values that are greater (for created events) or lower (for deleted events) than the
existing sequencer. If this condition is met, then the existing object is updated, and the old event is returned by the
database to be reinserted. If it is not met, then the event is inserted normally.

[clients]: src/clients
[database]: src/database
[events]: src/events
[handlers]: src/handlers
[env]: src/env.rs
[error]: src/error.rs
[mockall]: https://github.com/asomers/mockall
[s3-events]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html