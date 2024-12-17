from django.db import models

from app.fields import OrcaBusIdField
from app.models.base import BaseModel, BaseManager, BaseHistoricalRecords

class ContactManager(BaseManager):
    pass


class Contact(BaseModel):
    objects = ContactManager()

    orcabus_id = OrcaBusIdField(primary_key=True, prefix='ctc')
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
    history = BaseHistoricalRecords()
