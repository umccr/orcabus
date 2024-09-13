import ulid
from django.db import models
from simple_history.models import HistoricalRecords

from app.models.contact import Contact
from app.models.base import BaseModel, BaseManager


class ProjectManager(BaseManager):
    pass


class Project(BaseModel):
    orcabus_id_prefix = 'prj'
    objects = ProjectManager()
    history = HistoricalRecords()

    project_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    # Relationships
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = self.orcabus_id_prefix + '.' + ulid.new().str
        super().save(*args, **kwargs)
