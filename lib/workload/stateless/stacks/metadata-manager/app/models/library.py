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


class LibraryProjectLink(models.Model):
    """
    This is just a many-many link between Library and Project. We need to create this model so we could override the
    'db_column' field for the foreign keys. This make it less confusion between the 'project_id' and 'orcabus_id'
    in the schema.
    """
    library = models.ForeignKey('Library', on_delete=models.CASCADE, db_column='library_orcabus_id')
    project = models.ForeignKey('Project', on_delete=models.CASCADE, db_column='project_orcabus_id')


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
    sample = models.ForeignKey(Sample, on_delete=models.SET_NULL, blank=True, null=True,
                               db_column='sample_orcabus_id')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=True, null=True,
                                db_column='subject_orcabus_id')
    project_set = models.ManyToManyField(Project, through=LibraryProjectLink, related_name='library_set',
                                         blank=True)

    # history
    history = HistoricalRecords(m2m_fields=[project_set])
