## Default target
default: help

install: build
all: build

## Build related commands
build:
	@go build -o build
test:
	@go test
lint:
	@go fmt
golangci-lint:
	@golangci-lint run
check: lint golangci-lint

## Clean
clean:
	@go mod tidy

## Help text
help:
	@printf "The attribute annotator Makefile.\n\n"
	@printf "Usage: make <target>\n"

# No targets are files, so they are all PHONY.
.PHONY: *
