from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.analysis_context import AnalysisContext


class AnalysisManager(OrcaBusBaseManager):
    pass


class Analysis(OrcaBusBaseModel):
    class Meta:
        unique_together = ["analysis_name", "analysis_version"]

    id = models.BigAutoField(primary_key=True)

    analysis_name = models.CharField(max_length=255)
    analysis_version = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=255)

    allowed_contexts = models.ManyToManyField(AnalysisContext)

    objects = AnalysisManager()

    def __str__(self):
        return f"ID: {self.id}, analysis_name: {self.analysis_name}, analysis_version: {self.analysis_version}"

    def to_dict(self):
        return {
            "id": self.id,
            "analysis_name": self.analysis_name,
            "analysis_version": self.analysis_version,
            "description": self.description,
            "status": self.status
        }
