#!/usr/bin/env python

from enum import Enum


class Ethnicity(Enum):
    HISPANIC_OR_LATINO = "hispanic_or_latino"
    NOT_HISPANIC_OR_LATINO = "not_hispanic_or_latino"
    NOT_REPORTED = "not_reported"
    UNKNOWN = "unknown"
