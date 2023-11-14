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
	@npx generate queries --target ts --file --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret
	@npx generate edgeql-js --target ts --output-dir dbschema/edgeql-js --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret
	@npx generate interfaces --file dbschema/interfaces.ts --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret

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

# Inserting scenarios
insert-scenario-2:
	@yarn run insert-scenario-2

# Shortcut of edgedb cli
edgedb:
	@edgedb --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret
edgedb-ui:
	@edgedb ui --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure --no-server-check # pragma: allowlist secret
edgedb-migrate:
	@edgedb migrate --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret
edgedb-migration-create:
	@edgedb migration create --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret
