#!/usr/bin/env python

from . import BaseClass


class MedicalRecordNumber(BaseClass):
    from ..pieriandx_models.medical_record_number import MedicalRecordNumber
    _model = MedicalRecordNumber


