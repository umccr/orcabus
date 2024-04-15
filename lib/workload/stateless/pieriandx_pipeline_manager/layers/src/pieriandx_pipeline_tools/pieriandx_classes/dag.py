#!/usr/bin/env python

from . import BaseClass


class Dag(BaseClass):
    from ..pieriandx_models.dag import Dag
    _model = Dag


