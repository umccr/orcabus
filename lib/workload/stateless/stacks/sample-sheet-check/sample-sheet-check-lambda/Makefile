# Makefile for Python project

# Variables
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
TEST_DIR = tests

# Create virtual environment
$(VENV_DIR)/bin/activate: requirements.txt
	python3 -m venv $(VENV_DIR)
	$(PIP) install -r requirements.txt

# Install dependencies
install: $(VENV_DIR)/bin/activate

# Run tests
test: install
	$(PYTHON) -m unittest discover $(TEST_DIR)

# Clean up
clean:
	rm -rf $(VENV_DIR)
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

.PHONY: install test clean
