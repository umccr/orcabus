import ulid
from django.db import models
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class SubjectManager(BaseManager):
    None


class Subject(BaseModel):
    orcabus_id_prefix = 'sbj'

    objects = SubjectManager()

    subject_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = self.orcabus_id_prefix + '.' + ulid.new().str
        super().save(*args, **kwargs)
