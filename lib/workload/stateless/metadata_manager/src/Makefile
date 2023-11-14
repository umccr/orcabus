install:
	@yarn install

up:
	@docker compose up -d

down:
	@docker compose down

stop:
	@docker compose down

edgetypes:
	@npx generate queries --target ts --file --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret
	@npx generate edgeql-js --target ts --output-dir dbschema/edgeql-js
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

test:
	@yarn test

start:
	@yarn start

edgedb:
	@edgedb --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret
edgedb-ui:
	@edgedb ui --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure --no-server-check # pragma: allowlist secret
edgedb-migrate:
	@edgedb migrate --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret

edgedb-migration-create:
	@edgedb migration create --dsn edgedb://orcabus_admin:admin@localhost:5656 --tls-security insecure # pragma: allowlist secret