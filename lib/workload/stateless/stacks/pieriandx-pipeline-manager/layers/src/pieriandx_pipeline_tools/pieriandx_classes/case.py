#!/usr/bin/env python3
from . import BaseClass


class CaseCreation(BaseClass):
    from ..pieriandx_models.case_creation import CaseCreation
    _model = CaseCreation


class IdentifiedCaseCreation(BaseClass):
    from ..pieriandx_models.case_creation import IdentifiedCaseCreation
    _model = IdentifiedCaseCreation


class DeIdentifiedCaseCreation(BaseClass):
    from ..pieriandx_models.case_creation import DeIdentifiedCaseCreation
    _model = DeIdentifiedCaseCreation
