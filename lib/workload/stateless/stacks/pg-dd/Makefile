.PHONY: *

install:
	@poetry update

lint: install
	@poetry run ruff format .

check: lint
	@poetry run ruff check .

local: install
	@poetry run local