from django.db import models

from app.models.base import BaseModel, BaseManager, BaseHistoricalRecords


class SubjectManager(BaseManager):
    pass


class SubjectIndividualLink(models.Model):
    """
    This is just a many-many link between Subject and Individual. Creating this model allow to override the 'db_column'
    field for foreign keys that makes it less confusion between the 'subject_id' and 'orcabus_id' in the schema.
    """
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, db_column='subject_orcabus_id')
    individual = models.ForeignKey('Individual', on_delete=models.CASCADE, db_column='individual_orcabus_id')


class Subject(BaseModel):
    orcabus_id_prefix = 'sbj.'
    objects = SubjectManager()
    subject_id = models.CharField(
        unique=True,
        blank=True,
        null=True
    )

    # Relationships
    individual_set = models.ManyToManyField('Individual', through=SubjectIndividualLink,
                                            related_name='subject_set', blank=True)

    # history
    history = BaseHistoricalRecords(m2m_fields=[individual_set])
