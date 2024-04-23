.PHONY: test

install:
	@yarn install




up:
	@docker compose up --wait -d

down:
	@docker compose down

# The default outer `tests` target only run the top level cdk application unit tests under `./test`
test: up down
