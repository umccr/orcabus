.PHONY: *

DB_HOSTNAME ?= localhost
DB_PORT ?= 5432

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

## docker - psql
reset-db:
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(DB_HOSTNAME) -U orcabus -d orcabus -c "DROP DATABASE IF EXISTS metadata_manager;"
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(DB_HOSTNAME) -U orcabus -d orcabus -c "CREATE DATABASE metadata_manager;"

psql:
	@docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h $(DB_HOSTNAME) -U orcabus -d metadata_manager

# database operation
db-dump:
	mkdir -p data
	docker run --rm \
	-v $(shell pwd):/data \
	-e PGPASSWORD=orcabus \
	--network=metadata-manager_default \
	postgres:15.4 \
	pg_dump -h orcabus_db -U orcabus -d metadata_manager | gzip > data/mm_dump.sql.gz

s3-dump-upload:
	@aws s3 cp data/mm_dump.sql.gz s3://orcabus-test-data-843407916570-ap-southeast-2/metadata-manager/mm_dump.sql.gz

s3-dump-download:
	@aws s3 cp s3://orcabus-test-data-843407916570-ap-southeast-2/metadata-manager/mm_dump.sql.gz data/mm_dump.sql.gz

db-load-data: reset-db
	@gunzip -c data/mm_dump.sql.gz | docker exec -i orcabus_db psql -U orcabus -d metadata_manager >/dev/null

s3-dump-download-if-not-exists:
		@if [ -f "data/mm_dump.sql.gz" ]; then \
			echo "Using existing sql dump from './data/mm_dump.sql.gz"; \
		else \
			echo "Downloading sql dump from './data/mm_dump.sql.gz"; \
			$(MAKE) s3-dump-download; \
		fi

s3-load: s3-dump-download-if-not-exists db-load-data

# application

start: migrate
	@python manage.py runserver

docker-start: migrate
	@python manage.py runserver 0.0.0.0:8000

stop: down

loaded-start: up s3-load start

makemigrations:
	@python manage.py makemigrations

migrate:
	@python manage.py migrate

mock: reset-db migrate
	@python manage.py insert_mock_data

suite:
	@python manage.py test --parallel

coverage:
	@coverage run manage.py test
	@coverage report -m

# full mock suite test pipeline - install deps, bring up compose stack, run suite, bring down compose stack
test: install up suite down
