.PHONY: test

install:
	@yarn install
	@find ./lib -name 'requirements.txt' -exec pip install -r {} \;
	@pip install -r requirements-dev.txt
	@pre-commit install

check:
	@pre-commit run --all-files

build:
	for dir in $(shell find ./lib/workload/stateless/layers -maxdepth 1 -mindepth 1 -type d -exec basename {} \;); do ./lib/workload/stateless/layers/create_layer_package.sh $$dir; done

test:
	@yarn test
	@pytest
