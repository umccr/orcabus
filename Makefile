.PHONY: test

install:
	@yarn install
	@find ./lib -name 'requirements.txt' -exec pip install -r {} \;
	@pip install -r requirements-dev.txt
	@pre-commit install

check:
	@yarn audit
	@yarn lint
	@yarn prettier
	@pre-commit run --all-files

test:
	@yarn test
	@pytest

build:
	@for dir in $(shell find ./lib/workload/stateless/layers -maxdepth 1 -mindepth 1 -type d -exec basename {} \;); do ./lib/workload/stateless/layers/create_layer_package.sh $$dir; done

clean:
	@yarn clean
	@for zf in $(shell find ./lib/workload/stateless/layers -maxdepth 1 -mindepth 1 -type f -iname '*.zip'); do rm -v $$zf; done
