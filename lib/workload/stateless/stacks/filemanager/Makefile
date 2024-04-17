.EXPORT_ALL_VARIABLES:

## Database host ip address
FILEMANAGER_DATABASE_HOST ?= 0.0.0.0
## Database port
FILEMANAGER_DATABASE_PORT ?= 4321
## Database connection url
DATABASE_URL ?= postgresql://filemanager:filemanager@${FILEMANAGER_DATABASE_HOST}:${FILEMANAGER_DATABASE_PORT}/filemanager #pragma: allowlist secret
## Override the default project name
DOCKER_PROJECT_NAME ?= filemanager

## Default target
default: help

install: build
all: build

## Docker related targets
up:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" up --wait -d
down:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" down
docker-postgres:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" up --wait -d postgres --build
docker-clean:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" down --volumes
docker-build:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" build
docker-run: docker-build
	# Run the filemanager postgres service using an arbitrary host and port.
	@FILEMANAGER_DATABASE_HOST=0.0.0.0 FILEMANAGER_DATABASE_PORT=0 \
	docker compose -p "$(DOCKER_PROJECT_NAME)" run -d --service-ports postgres | xargs -I {} docker port {} 4321
docker-find:
	# Find a running filemanager docker container.
	@docker ps --filter name=$(DOCKER_PROJECT_NAME) --latest --format "{{.ID}}" | xargs -I {} docker port {} 4321

## Build related commands
build: docker-postgres
	@cargo build --all-features --all-targets
watch: docker-postgres
	@cargo watch -w *.toml -w *.rs
test: docker-postgres
	@cargo test --all-features --all-targets
test-ignored: docker-postgres
	@cargo test --all-features --all-targets -- --ignored
lint:
	@cargo fmt --check
lint-fix:
	@cargo fmt
clippy: docker-postgres
	cargo clippy --all-targets --all-features
check: lint clippy
check-fix: lint-fix clippy

## Clean
clean: docker-clean
	@cargo clean

## Database related targets
psql:
	@docker compose exec postgres psql filemanager -U filemanager

## Help text
help:
	@printf "The filemanager Makefile.\n\n"
	@printf "Usage: make <target> [POSTGRES_DATABASE_URL=<database_url>]\n"

# No targets are files, so they are all PHONY.
.PHONY: *
