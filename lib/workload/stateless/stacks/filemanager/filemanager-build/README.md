# filemanager-build

This crate contains code executed by filemanager during the build phase. It is responsible for creating/pre-compiling
any SQL queries, such as sea-orm entities, or pre-compiled queries, and migrating databases. Any code that should be
executed before compiling the [filemanager] crate should go here.

## Code generation

Parts of this code perform code generation using libraries such as [syn] - a Rust syntax tree parser. The syn library
is typically used when writing procedural macros (such as `#[derive(..)]` macros), however in this case it is useful
to generate helper code such as database entities or OpenAPI attributes that don't typically fit under procedural
macro functionality.

In general, code generation outputs in build scripts should go inside the `OUT_DIR` path set by Cargo when executing the
`build.rs` script.

## Project Layout

This crate is divided into the following modules.

* [error]: Error functionality and code, primarily written using miette in order to facilitate user-friendly build errors.
* [gen_entities]: Generates database entities using [sea-orm-cli] library.
* [gen_openapi]: Generates OpenAPI helper attributes for [utoipa].

[filemanager]: ../filemanager
[sea-orm-cli]: https://www.sea-ql.org/SeaORM/docs/generate-entity/sea-orm-cli/
[miette]: https://docs.rs/miette/latest/miette/
[utoipa]: https://github.com/juhaku/utoipa
[syn]: https://docs.rs/syn/latest/syn/