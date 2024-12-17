from django.db import models

from workflow_manager.fields import OrcaBusIdField
from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.analysis_context import AnalysisContext
from workflow_manager.models.workflow import Workflow


class AnalysisManager(OrcaBusBaseManager):
    pass


class Analysis(OrcaBusBaseModel):
    class Meta:
        unique_together = ["analysis_name", "analysis_version"]

    orcabus_id = OrcaBusIdField(primary_key=True, prefix='ana')
    analysis_name = models.CharField(max_length=255)
    analysis_version = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=255)

    # relationships
    contexts = models.ManyToManyField(AnalysisContext)
    workflows = models.ManyToManyField(Workflow)

    objects = AnalysisManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, analysis_name: {self.analysis_name}, analysis_version: {self.analysis_version}"
