from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class SubjectManager(BaseManager):
    None


class Subject(BaseModel):
    objects = SubjectManager()

    internal_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    history = HistoricalRecords()
