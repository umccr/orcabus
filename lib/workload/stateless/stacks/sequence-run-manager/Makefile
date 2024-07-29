.EXPORT_ALL_VARIABLES:
DJANGO_SETTINGS_MODULE = sequence_run_manager.settings.local

DB_HOSTNAME ?= localhost
DB_PORT ?= 5432

.PHONY: test suite

install:
	@pip install -r deps/requirements-dev.txt

check: lint

lint:
	@black -t py312 --check . --exclude .venv

lint-fix:
	@black -t py312 . --exclude .venv

# full mock suite test pipeline - install deps, bring up compose stack, run suite, bring down compose stack
test: install up suite down

suite:
	@python manage.py test

migrate:
	@python manage.py migrate

load: migrate
	@python manage.py generate_mock_data

start: migrate
	@python manage.py runserver_plus 0.0.0.0:8000

openapi:
	@python manage.py generateschema > orcabus.sequencerunmanager.openapi.yaml

validate: openapi
	@python -m openapi_spec_validator orcabus.sequencerunmanager.openapi.yaml

coverage: install up migrate
	@echo $$DJANGO_SETTINGS_MODULE
	@coverage run --source='.' manage.py test

report:
	@coverage report -m
	@coverage html

up:
	@docker compose up --wait -d

down:
	@docker compose down

stop: down

ps:
	@docker compose ps

psql:
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h 0.0.0.0 -d sequence_run_manager -U orcabus

# database operation

reset-db:
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(DB_HOSTNAME) -U orcabus -d orcabus -c "DROP DATABASE IF EXISTS sequence_run_manager;"
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(DB_HOSTNAME) -U orcabus -d orcabus -c "CREATE DATABASE sequence_run_manager;"

s3-dump-download:
	@aws s3 cp s3://orcabus-test-data-843407916570-ap-southeast-2/sequence-run-manager/srm_dump.sql.gz data/srm_dump.sql.gz

db-load-data: reset-db
	@gunzip -c data/srm_dump.sql.gz | docker exec -i orcabus_db psql -U orcabus -d sequence_run_manager >/dev/null

s3-dump-download-if-not-exists:
		@if [ -f "data/srm_dump.sql.gz" ]; then \
			echo "Using existing sql dump from './data/srm_dump.sql.gz"; \
		else \
			echo "Downloading sql dump from './data/srm_dump.sql.gz"; \
			$(MAKE) s3-dump-download; \
		fi

s3-load: s3-dump-download-if-not-exists db-load-data
