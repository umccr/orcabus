#!/usr/bin/env python

from . import BaseClass


class MedicalFacility(BaseClass):
    from ..pieriandx_models.medical_facility import MedicalFacility
    _model = MedicalFacility


