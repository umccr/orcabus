.PHONY: test

install:
	@corepack enable
	@yarn install --immutable

up:
	@docker compose up --wait -d

down:
	@docker compose down

suite:
	@yarn test --silent --forceExit

# The default outer `tests` target only run the top level cdk application unit tests under `./test`
test: install up suite down
