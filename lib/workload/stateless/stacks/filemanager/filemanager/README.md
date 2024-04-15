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

[clients]: src/clients
[database]: src/database
[events]: src/events
[handlers]: src/handlers
[env]: src/env.rs
[error]: src/error.rs
[mockall]: https://github.com/asomers/mockall
[s3-events]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html