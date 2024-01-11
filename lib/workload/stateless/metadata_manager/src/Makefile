EDGEDB_HOST ?= localhost

# Installation
install:
	@yarn install

# To run docker compose
up:
	@docker compose up -d

down:
	@docker compose down

stop:
	@docker compose down

# Build the app for deployment

edgetypes:
	@yarn run -B generate queries --target ts --file --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
	@yarn run -B generate edgeql-js --target ts --output-dir dbschema/edgeql-js --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
	@yarn run -B generate interfaces --file dbschema/interfaces.ts --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
	@yarn run ts-to-zod dbschema/queries.ts dbschema/queriesZodSchema.ts --skipValidation

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
test:
	@yarn test

# Starting server
start: edgetypes
	@yarn start
start-scenario-1: edgetypes
	@yarn run insert-scenario-1
	@yarn start

# Start in watch mode
watch: edgetypes
	@yarn run insert-scenario-1
	@yarn watch

# Inserting scenarios
insert-scenario-2:
	@yarn run insert-scenario-2

# Shortcut of edgedb cli
edgedb:
	@edgedb --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
edgedb-ui:
	@edgedb ui --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure --no-server-check # pragma: allowlist secret
edgedb-migrate:
	@edgedb migrate --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
edgedb-migration-create:
	@edgedb migration create --dsn edgedb://orcabus_admin:admin@$(EDGEDB_HOST):5656 --tls-security insecure # pragma: allowlist secret
