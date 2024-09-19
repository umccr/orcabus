from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class SubjectManager(BaseManager):
    pass


class Subject(BaseModel):
    orcabus_id_prefix = 'sbj.'
    objects = SubjectManager()
    subject_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    # Relationships
    individual_set = models.ManyToManyField('Individual', related_name='subject_set', blank=True)

    # history
    history = HistoricalRecords(m2m_fields=[individual_set])
