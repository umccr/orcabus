import ulid
from django.db import models
from simple_history.models import HistoricalRecords

from app.models.contact import Contact
from app.models.base import BaseModel, BaseManager


class ProjectManager(BaseManager):
    pass


class Project(BaseModel):
    orcabus_id_prefix = 'prj.'
    objects = ProjectManager()

    project_id = models.CharField(
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

    # Relationships
    contact_set = models.ManyToManyField(Contact, related_name='project_set', blank=True, )

    # history
    history = HistoricalRecords(m2m_fields=[contact_set])
