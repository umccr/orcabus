import ulid
from django.db import models
from simple_history.models import HistoricalRecords

from app.models.base import BaseModel, BaseManager


class ContactManager(BaseManager):
    pass


class Contact(BaseModel):
    orcabus_id_prefix = 'cnt'
    objects = ContactManager()

    contact_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = self.orcabus_id_prefix + '.' + ulid.new().str
        super().save(*args, **kwargs)
