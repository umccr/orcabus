from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class ContactManager(BaseManager):
    pass


class Contact(BaseModel):
    orcabus_id_prefix = 'ctc.'
    objects = ContactManager()

    contact_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )
    name = models.CharField(
        blank=True,
        null=True
    )
    description = models.CharField(
        blank=True,
        null=True
    )
    email = models.EmailField(
        blank=True,
        null=True
    )

    # history
    history = HistoricalRecords()
