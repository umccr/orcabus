#!/usr/bin/env python3

from enum import Enum


class Gender(Enum):
    UNKNOWN = "unknown"
    MALE = "male"
    FEMALE = "female"
    UNSPECIFIED = "unspecified"
    OTHER = "other"
    AMBIGUOUS = "ambiguous"
    NOT_APPLICABLE = "not_applicable"
