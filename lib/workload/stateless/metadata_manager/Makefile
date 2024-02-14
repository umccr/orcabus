EDGEDB_HOST ?= localhost

# installation
install:
	@yarn install

# docker compose shortcut
up:
	@docker compose up --wait -d

down:
	@docker compose down

stop:
	@docker compose down

docker-edgedb:
	@docker compose up --wait -d edgedb

# asset build
edgetypes: | docker-edgedb
	@yarn run -B generate queries --target ts --file --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
	@yarn run -B generate edgeql-js --target ts --output-dir dbschema/edgeql-js --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
	@yarn run -B generate interfaces --file dbschema/interfaces.ts --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
	@yarn run ts-to-zod dbschema/queries.ts dbschema/queriesZodSchema.ts


build: edgetypes
	@rm -rf asset
	@mkdir -p asset
	@yarn run build-src
	@cd dist && zip -r ../asset/src.zip .

	@mkdir -p nodejs
	@cp -r node_modules ./nodejs
	@zip -r asset/dependency.zip nodejs
	@rm -rf nodejs

# Testing

# full test pipeline
test: install docker-edgedb edgetypes suite down

suite:
	@yarn test

# Starting server
start: up

stop: down 

# development
start-dev: docker-edgedb edgetypes
	@yarn start

watch-dev: docker-edgedb edgetypes
	@yarn run insert-scenario-1
	@yarn watch

insert-scenario-1:
	@yarn run insert-scenario-1

insert-scenario-2:
	@yarn run insert-scenario-2

# Shortcut of edgedb cli
edgedb: | docker-edgedb
	@edgedb --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
edgedb-ui: | docker-edgedb
	@edgedb ui --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure --no-server-check # pragma: allowlist secret
edgedb-migrate: | docker-edgedb
	@edgedb migrate --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
edgedb-migration-create: | docker-edgedb
	@edgedb migration create --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
