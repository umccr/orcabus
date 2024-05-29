install:
	@pip install -r deps/requirements-test.txt

test-translator-service:
	@echo "Running tests for translator service"
	@PYTHONPATH=./translator_service:$$PYTHONPATH \
	python -m unittest translator_service/tests/test_icav2_event_translator.py
	@echo "Tests for translator service passed"

test: install test-translator-service
