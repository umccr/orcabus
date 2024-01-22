.PHONY: test suite

install:
	@pip install -r requirements-dev.txt

check: lint

lint:
	@black -t py312 --check ./src --exclude skel --exclude .venv

lint-fix:
	@black -t py312 ./src --exclude skel --exclude .venv

# full mock suite test pipeline - install deps, bring up compose stack, wait a bit, run suite, bring down compose stack
test: install up wait suite down

# heuristic wait 8s to make sure the database is fully up
# todo we could improve this
wait:
	@sleep 8

suite:
	@python manage.py test

up:
	@docker compose up -d

down:
	@docker compose down

stop: down

ps:
	@docker compose ps

psql:
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h 0.0.0.0 -d orcabus -U orcabus
