from django.db import models

from app.models.contact import Contact
from app.models.base import BaseModel, BaseManager, BaseHistoricalRecords


class ProjectManager(BaseManager):
    pass


class ProjectContactLink(models.Model):
    """
    This is just a many-many link between Project and Contact. We need to create this model so we could override the
    'db_column' field for the foreign keys. This make it less confusion between the 'project_id' and 'orcabus_id'
    in the schema.
    """
    project = models.ForeignKey('Project', on_delete=models.CASCADE, db_column='project_orcabus_id')
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE, db_column='contact_orcabus_id')


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
    contact_set = models.ManyToManyField(Contact, through=ProjectContactLink, related_name='project_set',
                                         blank=True)

    # history
    history = BaseHistoricalRecords(m2m_fields=[contact_set])
