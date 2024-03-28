import logging

from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseManager, BaseModel
from app.models.lab.specimen import Specimen

logger = logging.getLogger(__name__)


class WorkflowType(models.TextChoices):
    CLINICAL = 'clinical'
    RESEARCH = 'research'
    QC = 'qc'
    CONTROL = 'control'
    BCL = 'bcl'
    MANUAL = 'manual'


class Phenotype(models.TextChoices):
    NORMAL = 'normal'
    TUMOR = 'tumor'
    NEGATIVE_CONTROL = 'negative-control'


class Quality(models.TextChoices):
    VERY_POOR = 'very-poor'
    POOR = 'poor'
    GOOD = 'good'
    BORDERLINE = 'borderline'


class LibraryType(models.TextChoices):
    TEN_X = '10X'
    CT_DNA = 'ctDNA'
    CT_TSO = 'ctTSO'
    EXOME = 'exome'
    METAGENM = 'Metagenm'
    METHYL_SEQ = 'MethylSeq'
    TSO_DNA = 'TSO-DNA'
    TSO_RNA = 'TSO-RNA'
    WGS = 'WGS'
    WTS = 'WTS'
    BIMODAL = 'BiModal'
    OTHER = 'other'


class LibraryManager(BaseManager):
    None


class Library(BaseModel):
    objects = LibraryManager()

    internal_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    phenotype = models.CharField(
        choices=Phenotype.choices,
        blank=True,
        null=True
    )
    workflow = models.CharField(
        choices=WorkflowType.choices,
        blank=True,
        null=True
    )
    quality = models.CharField(
        choices=Quality.choices,
        blank=True,
        null=True
    )
    type = models.CharField(
        choices=LibraryType.choices,
        blank=True,
        null=True
    )
    assay = models.CharField(
        blank=True,
        null=True
    )
    coverage = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True,
        null=True
    )

    specimen = models.ForeignKey(Specimen, on_delete=models.SET_NULL, blank=True, null=True)
    history = HistoricalRecords()
