import ulid
from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class IndividualManager(BaseManager):
    pass


class Individual(BaseModel):
    orcabus_id_prefix = 'idv'
    objects = IndividualManager()
    history = HistoricalRecords()

    individual_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = self.orcabus_id_prefix + '.' + ulid.new().str
        super().save(*args, **kwargs)
