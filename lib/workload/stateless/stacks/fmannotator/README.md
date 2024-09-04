# FMAnnotator

The FMAnnotator service annotates records using the FileManager API.

## Development

This service is written in Go, which should be [installed][golang]. Please also install [golangci-lint] to run lints on
the codebase.

This project is organised using the Go Lambda function CDK, and contains Lambda function handlers under [`cmd`][cmd]

Makefile is used to simplify development. Tests can be run by using:

```sh
make test
```

Lints and checks can be run using:

```sh
make check
```

To update the [go.mod][go-mod] and download any new go modules:

```sh
make clean
```

## Project layout

This service has the following structure:

* [cmd]: The Lambda handler `main.go` functions.
* [deploy]: CDK deployment code.
* [fixtures]: Database fixtures and test data.
* [internal]: Internal package containing common test code.
* [schema]: Generated EventBridge code-bindings.

Top-level `.go` files contain library related code which implements the functionality of the FMAnnotator.
Tests are defined using the `_test.go` suffix.

[golang]: https://go.dev/doc/install
[golangci-lint]: https://golangci-lint.run/welcome/install/#local-installation
[cmd]: cmd
[api]: api.go
[config]: config.go
[handlers]: handlers.go
[internal]: internal
[fixtures]: fixtures
[schema]: schema
[go-mod]: go.mod
