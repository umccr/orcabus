import logging

from django.db import models
from django.db.models import QuerySet
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager
from app.models.lab.subject import Subject


class Source(models.TextChoices):
    ASCITES = "ascites"
    BLOOD = "blood"
    BONE_MARROW = "bone-marrow"
    BUCCAL = "buccal"
    CELLLINE = "cell-line"
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
    TISSUE = "tissue"
    SKIN = "skin"
    WATER = "water"


class SpecimenManager(BaseManager):
    None


class Specimen(BaseModel):
    objects = SpecimenManager()

    internal_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    source = models.CharField(choices=Source.choices, blank=True, null=True)

    subjects = models.ManyToManyField(Subject, blank=True)
    history = HistoricalRecords(m2m_fields=[subjects])
