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


# database operation
db-dump:
	mkdir -p data
	docker run --rm \
	-v $(shell pwd):/data \
	-e PGPASSWORD=orcabus \
	--network=metadata-manager_default \
	postgres:15.4 \
	pg_dump -h orcabus_db -U orcabus -d orcabus | gzip > data/mm_dump.sql.gz

s3-dump-upload:
	@aws s3 cp data/mm_dump.sql.gz s3://orcabus-test-data-843407916570-ap-southeast-2/metadata-manager/mm_dump.sql.gz

s3-dump-download:
	@aws s3 cp s3://orcabus-test-data-843407916570-ap-southeast-2/metadata-manager/mm_dump.sql.gz data/mm_dump.sql.gz

db-load-data:
	@gunzip -c data/mm_dump.sql.gz | docker exec -i orcabus_db psql -U orcabus -d orcabus >/dev/null

s3-load: | s3-dump-download down up db-load-data

