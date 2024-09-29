from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.fields import OrcabusIdField


class AnalysisContextManager(OrcaBusBaseManager):
    pass


class AnalysisContext(OrcaBusBaseModel):

    orcabus_id = OrcabusIdField(prefix='ctx', primary_key=True)
    context_id = models.CharField(max_length=255)

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=255)

    objects = AnalysisContextManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, name: {self.name}, status: {self.status}"

    def to_dict(self):
        return {
            "orcabus_id": self.orcabus_id,
            "context_id": self.context_id,
            "name": self.name,
            "status": self.status,
            "description": self.description
        }
