import logging

from django.db import models
from django.db.models import QuerySet
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class IndividualManager(BaseManager):
    None


class Individual(BaseModel):
    objects = IndividualManager()

    internal_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    history = HistoricalRecords()
