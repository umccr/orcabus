install:
	@pip install -r requirements-dev.txt
	@pre-commit install

check:
	@pre-commit run --all-files

run:
	sam local invoke

build:
	for dir in $(shell find ./lambdas/layers -maxdepth 1 -mindepth 1 -type d -exec basename {} \;); do ./lambdas/layers/create_layer_package.sh $$dir; done
	cdk synth

deploy: build
	cdk deploy OrcaBus
	cdk deploy OrcaBusSchemaStack
