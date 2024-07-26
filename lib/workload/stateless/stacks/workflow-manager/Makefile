.EXPORT_ALL_VARIABLES:
DJANGO_SETTINGS_MODULE = workflow_manager.settings.local
EVENT_BUS_NAME = mock-bus

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

start: migrate
	@python manage.py runserver_plus 0.0.0.0:8000

openapi:
	@python manage.py generateschema > orcabus.hlo.openapi.yaml

validate: openapi
	@python -m openapi_spec_validator orcabus.hlo.openapi.yaml

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
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h 0.0.0.0 -d orcabus -U orcabus
