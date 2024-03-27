from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager
from app.models.lab.individual import Individual


class SubjectManager(BaseManager):
    None


class Subject(BaseModel):
    objects = SubjectManager()

    internal_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    individual = models.ForeignKey(Individual, on_delete=models.SET_NULL, blank=True, null=True)
    history = HistoricalRecords()
