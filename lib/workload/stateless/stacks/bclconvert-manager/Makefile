install:
	@pip install -r deps/requirements-test.txt

test-translator-service:
	@python -m unittest translator_service/tests/test_icav2_event_translator.py

test: install test-translator-service
