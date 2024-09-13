import ulid
from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class SubjectManager(BaseManager):
    pass


class Subject(BaseModel):
    orcabus_id_prefix = 'sbj'
    objects = SubjectManager()
    history = HistoricalRecords()

    subject_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    external_subject_id = models.CharField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = self.orcabus_id_prefix + '.' + ulid.new().str
        super().save(*args, **kwargs)
