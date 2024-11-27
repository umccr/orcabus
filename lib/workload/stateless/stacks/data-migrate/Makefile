.PHONY: *

install:
	@poetry update

lint: install
	@poetry run ruff format .

check: lint
	@poetry run ruff check .

dm: install
	@poetry run dm $(COMMAND)

clean:
	rm -rf data && rm -rf .ruff_cache
