#!/usr/bin/env python

from . import BaseClass


class Disease(BaseClass):
    from ..pieriandx_models.disease import Disease
    _model = Disease


