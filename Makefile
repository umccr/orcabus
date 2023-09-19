.PHONY: test deep scan

install:
	@yarn install
	@find ./lib -name 'requirements.txt' -exec pip install -r {} \;
	@pip install -r requirements-dev.txt
	@pre-commit install

check:
	@yarn audit
	@yarn lint
	@yarn prettier
	@pre-commit run --all-files

scan:
	@trufflehog --debug --only-verified git file://./ --since-commit main --branch HEAD --fail

deep: scan
	@ggshield secret scan repo .

baseline:
	@detect-secrets scan --exclude-files '^(yarn.lock|.yarn/|.local/|openapi/)' > .secrets.baseline

build:
	@(cd lib/workload/stateless/metadata_manager/src && yarn && yarn edgetypes)

test:
	@yarn test
	@(cd lib/workload/stateless/sequence_run_manager/src && python manage.py test)

clean:
	@yarn clean
	@for zf in $(shell find ./lib/workload/stateless/layers -maxdepth 1 -mindepth 1 -type f -iname '*.zip'); do rm -v $$zf; done

up:
	@docker compose up -d

down:
	@docker compose down

stop:
	@docker compose down

ps:
	@docker compose ps

mysql:
	@docker exec -it orcabus_db mysql -h 0.0.0.0 -D orcabus -u root -proot
