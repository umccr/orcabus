.PHONY: test deep scan

install:
	@yarn install
	@pre-commit install

check:
	@yarn audit
	@yarn lint
	@yarn prettier
	@pre-commit run --all-files

scan:
	@trufflehog --debug --only-verified git file://./ --since-commit main --branch HEAD --fail

deep: scan
	@ggshield secret scan repo .

baseline:
	@detect-secrets scan --exclude-files '^(yarn.lock|.yarn/|.local/|openapi/)' > .secrets.baseline

# Test only section 
test-stateful:
	@yarn run test ./test/stateful
test-stateless:
	@yarn run test ./test/stateless

# Run all test suites for each app/microservice
# Each app root should have Makefile `test` target; that run your app test pipeline including compose stack up/down
# Note by running `make suite` target from repo root means your local dev env is okay with all app toolchains i.e.
# 	Python (conda or venv), Rust and Cargo, TypeScript and Node environment, Docker and Container runtimes
test-suite:
	@(cd lib/workload/stateless/stacks/sequence-run-manager && $(MAKE) test)
	@(cd lib/workload/stateless/stacks/metadata-manager && $(MAKE) test)
	@(cd lib/workload/stateless/stacks/filemanager && $(MAKE) test)
	@(cd lib/workload/stateless/stacks/postgres-manage && $(MAKE) test)

# The default outer `test` target only run the top level cdk application unit tests under `./test`
test: test-stateless test-stateful test-suite

clean:
	@yarn clean
	@#for zf in $(shell find ./lib/workload/stateless/layers -maxdepth 1 -mindepth 1 -type f -iname '*.zip'); do rm -v $$zf; done
