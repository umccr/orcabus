import logging

import ulid
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import QuerySet
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class IndividualManager(BaseManager):
    None


class Individual(BaseModel):
    orcabus_id_prefix = 'idv'
    objects = IndividualManager()

    internal_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = self.orcabus_id_prefix + '.' + ulid.new().str
        super().save(*args, **kwargs)
