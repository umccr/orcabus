import ulid
from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


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


class SampleManager(BaseManager):
    pass


class Sample(BaseModel):
    orcabus_id_prefix = 'smp.'
    objects = SampleManager()

    sample_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    external_sample_id = models.CharField(
        blank=True,
        null=True
    )
    source = models.CharField(choices=Source.choices, blank=True, null=True)

    # history
    history = HistoricalRecords()