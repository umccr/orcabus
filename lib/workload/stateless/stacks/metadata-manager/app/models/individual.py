from django.db import models

from app.fields import OrcaBusIdField
from app.models.base import BaseModel, BaseManager, BaseHistoricalRecords


class IndividualManager(BaseManager):
    pass


class Individual(BaseModel):
    objects = IndividualManager()

    orcabus_id = OrcaBusIdField(primary_key=True, prefix='idv')
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
    history = BaseHistoricalRecords()
