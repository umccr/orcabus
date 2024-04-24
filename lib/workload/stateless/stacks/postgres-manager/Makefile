.PHONY: test

install:
	@yarn install

up:
	@docker compose up --wait -d

down:
	@docker compose down

suite:
	yarn test --silent --forceExit

# The default outer `tests` target only run the top level cdk application unit tests under `./test`
test: up suite down
