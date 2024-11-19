.PHONY: *

install:
	@poetry update

lint: install
	@poetry run ruff format .

check: lint
	@poetry run ruff check .

cli: install
	@poetry run cli

clean:
	rm -rf data && rm -rf .ruff_cache