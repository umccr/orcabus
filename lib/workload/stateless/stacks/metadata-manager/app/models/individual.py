from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class IndividualManager(BaseManager):
    pass


class Individual(BaseModel):
    orcabus_id_prefix = 'idv.'
    objects = IndividualManager()

    individual_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    source = models.CharField(
        blank=True,
        null=True
    )

    # history
    history = HistoricalRecords()
