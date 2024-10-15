#!/usr/bin/env python3

from enum import Enum


class SequencingType(Enum):
    PAIRED_END = "pairedEnd"
    SINGLE_END = "singleEnd"
