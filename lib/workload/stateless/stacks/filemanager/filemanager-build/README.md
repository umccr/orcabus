# filemanager-build

This crate contains code executed by filemanager during the build phase. It is responsible for creating/pre-compiling
any SQL queries, such as sea-orm entities, or pre-compiled queries, and migrating databases. Any code that should be
executed before compiling the [filemanager] crate should go here.

[filemanager]: ../filemanager