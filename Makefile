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

test-stateful-iac:
	@yarn run test ./test/stateful

test-stateless-iac:
	@yarn run test ./test/stateless

# Run all test suites for each app/microservice/stack
# Each app root should have Makefile `test` target; that run your app test pipeline including compose stack up/down
# Note by running `make suite` target from repo root means your local dev env is okay with all app toolchains i.e.
# 	Python (conda or venv), Rust and Cargo, TypeScript and Node environment, Docker and Container runtimes
test-stateful-app-suite:
	@(cd lib/workload/stateful/stacks/postgres-manager && $(MAKE) test)

test-stateless-app-suite:
	@(cd lib/workload/stateless/stacks/sequence-run-manager && $(MAKE) test)
	@(cd lib/workload/stateless/stacks/metadata-manager && $(MAKE) test)
	@(cd lib/workload/stateless/stacks/filemanager && $(MAKE) test)
	@(cd lib/workload/stateless/stacks/bclconvert-manager && $(MAKE) test)
	@(cd lib/workload/stateless/stacks/workflow-manager && $(MAKE) test)

# The default outer `test` target run all test in this repo
test: test-stateful-iac test-stateless-iac test-stateful-app-suite test-stateless-app-suite

clean:
	@yarn clean
