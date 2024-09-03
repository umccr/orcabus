from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.analysis_context import AnalysisContext


class AnalysisRunManager(OrcaBusBaseManager):
    pass


class AnalysisRun(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    analysis_run_id = models.CharField(max_length=255, unique=True)

    analysis_run_name = models.CharField(max_length=255)
    comment = models.CharField(max_length=255)

    approval_context = models.ForeignKey(AnalysisContext, null=True, blank=True, on_delete=models.SET_NULL)
    project_context = models.ForeignKey(AnalysisContext, null=True, blank=True, on_delete=models.SET_NULL)

    objects = AnalysisRunManager()

    def __str__(self):
        return f"ID: {self.analysis_run_id}, analysis_run_name: {self.analysis_run_name}"

    def to_dict(self):
        return {
            "analysis_run_id": self.analysis_run_id,
            "analysis_run_name": self.analysis_run_name,
            "comment": self.comment,
            "approval_context": self.approval_context,
            "project_context": self.project_context
        }
