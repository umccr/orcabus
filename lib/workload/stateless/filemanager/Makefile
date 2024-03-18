POSTGRES_DATABASE_URL ?= postgresql://filemanager:filemanager@localhost:4321/filemanager #pragma: allowlist secret

export DATABASE_URL=$(POSTGRES_DATABASE_URL)

## Default target
default: help

install: build
all: build

## Docker related targets
up:
	@docker compose up --wait -d
down:
	@docker compose down
docker-postgres:
	@docker compose up --wait -d postgres
docker-clean:
	@docker compose down --volumes

## Build related commands
build: docker-postgres
	@cargo build --all-features --all-targets
watch: build
	@cargo watch -w *.toml -w *.rs
test: build
	@cargo test --all-features --all-targets
test-ignored: build
	@cargo test --all-features --all-targets -- --ignored
lint:
	@cargo fmt --check
lint-fix:
	@cargo fmt
clippy: build
	cargo clippy --all-targets --all-features
check: lint clippy
check-fix: lint-fix clippy

## Clean
clean: docker-clean
	@cargo clean

## Database related targets
psql:
	@docker exec -it filemanager_db psql filemanager -U filemanager

## Help text
help:
	@printf "The filemanager Makefile.\n\n"
	@printf "Usage: make <target> [POSTGRES_DATABASE_URL=<database_url>]\n"

# No targets are files, so they are all PHONY.
.PHONY: *
