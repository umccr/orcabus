#!/usr/bin/env python3

from os import environ

# Globals
SECTION_LEVEL = 2
TABLE_COUNT = 0

DYNAMODB_TABLE_NAME = environ['DYNAMODB_TABLE_NAME']
DYNAMODB_INDEX_NAME = environ['DYNAMODB_INDEX_NAME']  # "content-index"