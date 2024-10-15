#!/usr/bin/env python

from . import BaseClass


class Physician(BaseClass):
    from ..pieriandx_models.physician import Physician
    _model = Physician


