.EXPORT_ALL_VARIABLES:

## Database host ip address
FILEMANAGER_DATABASE_HOST ?= 0.0.0.0
## Database port
FILEMANAGER_DATABASE_PORT ?= 4321

## Database connection url
DATABASE_URL ?= postgresql://filemanager:filemanager@${FILEMANAGER_DATABASE_HOST}:${FILEMANAGER_DATABASE_PORT}/filemanager #pragma: allowlist secret
## Override the default project name
DOCKER_PROJECT_NAME ?= filemanager

## The links url.
FILEMANAGER_LINKS_URL ?= localhost:8000


## Default target
default: help

install: build
all: build

## Docker related targets
up:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" up --wait -d postgres
down:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" down
docker-postgres:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" up --wait -d postgres --build postgres
docker-clean:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" down --volumes postgres
docker-build:
	@docker compose -p "$(DOCKER_PROJECT_NAME)" build postgres
docker-run: docker-build
	# Run the filemanager postgres service using an arbitrary host and port.
	@FILEMANAGER_DATABASE_HOST=0.0.0.0 FILEMANAGER_DATABASE_PORT=0 \
	docker compose -p "$(DOCKER_PROJECT_NAME)" run -d --service-ports postgres | xargs -I {} docker port {} 4321
docker-find:
	# Find a running filemanager docker container.
	@docker ps --filter name=$(DOCKER_PROJECT_NAME)-postgres --latest --format "{{.ID}}" | xargs -I {} docker port {} | tail -n 1 | awk '{print $$NF}'
docker-api: docker-postgres
	# Run the local API server in a docker container.
	@docker compose -p "$(DOCKER_PROJECT_NAME)" up api

## Build related commands
entity: docker-postgres
	@cargo run -p filemanager-build -- --out-dir filemanager/src/database/entities
build: docker-postgres entity
	@cargo build --all-features --all-targets
watch: docker-postgres entity
	@cargo watch -w *.toml -w *.rs
test: docker-postgres
	@cargo test --all-features --all-targets
test-ignored: docker-postgres
	@cargo test --all-features --all-targets -- --ignored
lint:
	@cargo fmt --check
lint-fix:
	@cargo fmt
clippy: docker-postgres entity
	@cargo clippy --all-targets --all-features
check: lint clippy
check-fix: lint-fix clippy

## Clean
clean: docker-clean
	@cargo clean

## Database related targets
psql:
	@docker compose exec postgres psql filemanager -U filemanager
restore:
	@docker compose exec -T postgres pg_restore -U filemanager -d filemanager

## Targets related to top-level database management and S3.
reset-db:
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(FILEMANAGER_DATABASE_HOST) -U orcabus -d orcabus -c "DROP DATABASE IF EXISTS filemanager;" && \
	docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(FILEMANAGER_DATABASE_HOST) -U orcabus -d orcabus -c "CREATE DATABASE filemanager;"
	for file in database/migrations/*; do \
  	 	docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(FILEMANAGER_DATABASE_HOST) -U orcabus -d filemanager -c "$$(cat $$file)"; \
  	done
s3-dump-upload:
	@aws s3 cp data/fm_s3_objects_100000.csv.gz s3://orcabus-test-data-843407916570-ap-southeast-2/file-manager/fm_s3_objects_100000.csv.gz
s3-dump-download:
	@aws s3 cp s3://orcabus-test-data-843407916570-ap-southeast-2/file-manager/fm_s3_objects_100000.csv.gz data/fm_s3_objects_100000.csv.gz
db-load-data: reset-db
	@gunzip -c data/fm_s3_objects_100000.csv.gz | \
     docker exec -i orcabus_db psql -U orcabus -d filemanager -c "copy s3_object from stdin with (format csv, header);"
s3-dump-download-if-not-exists:
	@if [ -f "data/fm_s3_objects_100000.csv.gz" ]; then \
		echo "Using existing sql dumps from 'data/fm_s3_objects_100000.csv.gz"; \
	else \
		echo "Downloading sql dumps"; \
		$(MAKE) s3-dump-download; \
	fi
s3-load: s3-dump-download-if-not-exists db-load-data

## Local API server.
start: docker-postgres
	@cargo run -p filemanager-api-server $(ARGS)

## Help text
help:
	@printf "The filemanager Makefile.\n\n"
	@printf "Usage: make <target> [DATABASE_URL=<database_url>]\n"

# No targets are files, so they are all PHONY.
.PHONY: *
