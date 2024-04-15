#!/usr/bin/env python

from . import BaseClass


class Specimen(BaseClass):
    from ..pieriandx_models.specimen import Specimen
    _model = Specimen


class IdentifiedSpecimen(Specimen):
    from ..pieriandx_models.specimen import IdentifiedSpecimen
    _model = IdentifiedSpecimen


class DeIdentifiedSpecimen(Specimen):
    from ..pieriandx_models.specimen import DeIdentifiedSpecimen
    _model = DeIdentifiedSpecimen


