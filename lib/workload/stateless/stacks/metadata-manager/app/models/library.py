import logging

from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseManager, BaseModel
from app.models.subject import Subject
from app.models.sample import Sample
from app.models.project import Project

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
    VERY_POOR = 'very-poor', 'VeryPoor'
    POOR = 'poor'
    GOOD = 'good'
    BORDERLINE = 'borderline'


class LibraryType(models.TextChoices):
    TEN_X = '10X'
    BIMODAL = 'BiModal'
    CT_DNA = 'ctDNA'
    CT_TSO = 'ctTSO'
    EXOME = 'exome', "Exome"
    ME_DIP = 'MeDIP'
    METAGENM = 'Metagenm'
    METHYL_SEQ = 'MethylSeq'
    TSO_DNA = 'TSO-DNA', 'TSO_DNA'
    TSO_RNA = 'TSO-RNA', 'TSO_RNA'
    WGS = 'WGS'
    WTS = 'WTS'

    OTHER = 'other'


class LibraryManager(BaseManager):
    pass


class Library(BaseModel):
    orcabus_id_prefix = 'lib.'
    objects = LibraryManager()

    library_id = models.CharField(
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
    coverage = models.FloatField(
        blank=True,
        null=True
    )

    # Relationships
    sample = models.ForeignKey(Sample, on_delete=models.SET_NULL, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=True, null=True)
    project_set = models.ManyToManyField(Project, related_name='library_set', blank=True)

    # history
    history = HistoricalRecords(m2m_fields=[project_set])


def sanitize_library_coverage(value: str):
    """
    convert value that is valid in the tracking sheet to return a value that is recognizable by the Django Model
    """
    try:
        # making coverage is float-able type
        lib_coverage = float(value)
        return f'{lib_coverage}'

    except (ValueError, TypeError):
        return None

