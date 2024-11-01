from django.db import models

from app.models.base import BaseModel, BaseManager, BaseHistoricalRecords


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
    history = BaseHistoricalRecords()
