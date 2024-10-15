#!/usr/bin/env python3

from enum import Enum


class SampleType(Enum):
    PATIENTCARE = 'patientcare'
    CLINICAL_TRIAL = 'clinical_trial'
    VALIDATION = 'validation'
    PROFICIENCY_TESTING = 'proficiency_testing'
