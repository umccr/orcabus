import logging

import ulid
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import QuerySet
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager
from app.models.lab.subject import Subject


class Source(models.TextChoices):
    ASCITES = "ascites", "Ascites"
    BLOOD = "blood", "Blood"
    BONE_MARROW = "bone-marrow", "BoneMarrow"
    BUCCAL = "buccal"
    CELLLINE = "cell-line", "Cell_line"
    CFDNA = "cfDNA"
    CYST_FLUID = "cyst-fluid"
    DNA = "DNA"
    EYEBROW_HAIR = "eyebrow-hair"
    FFPE = "FFPE"
    FNA = "FNA"
    OCT = "OCT"
    ORGANOID = "organoid"
    PDX_TISSUE = "PDX-tissue"
    PLASMA_SERUM = "plasma-serum"
    RNA = "RNA"
    TISSUE = "tissue", "Tissue"
    SKIN = "skin"
    WATER = "water", "Water"


class SpecimenManager(BaseManager):
    pass


class Specimen(BaseModel):
    orcabus_id_prefix = 'spc'

    objects = SpecimenManager()

    specimen_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    source = models.CharField(choices=Source.choices, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=True, null=True)

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = self.orcabus_id_prefix + '.' + ulid.new().str
        super().save(*args, **kwargs)
