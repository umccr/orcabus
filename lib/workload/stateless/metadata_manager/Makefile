.PHONY: test suite

# installation
install:
	@pip install -r deps/requirements-dev.txt

# docker compose shortcut
up:
	@docker compose up --wait -d

down:
	@docker compose down

ps:
	@docker compose ps

# application

start: | up migrate
	@python manage.py runserver

stop: down

makemigrations:
	@python manage.py makemigrations

migrate:
	@python manage.py migrate

insert-data:
	@python manage.py insert_mock_data

suite:
	@python manage.py test

# full mock suite test pipeline - install deps, bring up compose stack, run suite, bring down compose stack
test: install up suite down

# psql
psql:
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h 0.0.0.0 -d orcabus -U orcabus
