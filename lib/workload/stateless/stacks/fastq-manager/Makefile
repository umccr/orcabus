.EXPORT_ALL_VARIABLES:

## Database port
FASTQ_MANAGER_DYNAMODB_PORT ?= 8456
FASTQ_MANAGER_API_PORT ?= 8457

## Database connection url
FASTQ_MANAGER_DYNAMODB_HOST ?= http://localhost:${FASTQ_MANAGER_DYNAMODB_PORT}

## Override the default table name
DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME ?= fastq_list_row

## Docker project name
FASTQ_MANAGER_DOCKER_PROJECT_NAME = fastq_manager

## Default target
default: help

install: build
all: build

# Up
dynamodb_up:
	mkdir -p docker/dynamodb
	@DYNAMODB_PORT=$(FASTQ_MANAGER_DYNAMODB_PORT) FASTQ_MANAGER_API_PORT=$(FASTQ_MANAGER_API_PORT) docker compose --project-name "$(FASTQ_MANAGER_DOCKER_PROJECT_NAME)" up --wait --force-recreate --detach dynamodb-local
build: dynamodb_up
	@sleep 2
	AWS_PROFILE=local AWS_ENDPOINT_URL="$(FASTQ_MANAGER_DYNAMODB_HOST)" TABLE_NAME="$(DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME)" bash -o xtrace create_table.sh
up: build
	@DYNAMODB_PORT=$(FASTQ_MANAGER_DYNAMODB_PORT) FASTQ_MANAGER_API_PORT=$(FASTQ_MANAGER_API_PORT) docker compose --project-name "$(FASTQ_MANAGER_DOCKER_PROJECT_NAME)" up --wait --force-recreate --detach fastapi

# Down
down:
	@docker compose --project-name "$(FASTQ_MANAGER_DOCKER_PROJECT_NAME)" down

## Clean
docker-clean:
	@docker container list --all --format '{{.Names}}' | grep 'dynamodb-local' && docker container stop dynamodb-local || true
	@docker container list --all --format '{{.Names}}' | grep 'dynamodb-local' && docker container rm dynamodb-local || true
	docker container list --all --format '{{.Names}}' | grep 'fastq-manager' && docker container stop fastq-manager || true
	docker container list --all --format '{{.Names}}' | grep 'fastq-manager' && docker container rm fastq-manager || true
	docker images --format '{{.Repository}}' | grep 'fastq_manager-fastapi' && docker image rm fastq_manager-fastapi || true
clean: docker-clean
	rm -rf docker

## Targets related to top-level database management and S3.
reset-db: clean up

# No targets are files, so they are all PHONY.
.PHONY: *
