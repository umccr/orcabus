# Define the path to the Lambda Layer
LAYER_PATH := ../../schemas-codebinding-layer/layers

# Default target
.PHONY: test

install:
	@pip install -r deps/requirements-test.txt

test: install
	@PYTHONPATH=$(LAYER_PATH):$$PYTHONPATH \
	python -m unittest tests/test_icav2_event_translator.py

# Clean environment - this is optional and just for explicit cleanup demonstration
.PHONY: clean
clean:
	@echo "Cleaning up environment..."
# No need to clean up in this setup, as changes to PYTHONPATH were not permanent