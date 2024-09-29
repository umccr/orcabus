from django.db import models

from workflow_manager.fields import OrcabusIdField
from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.analysis import Analysis
from workflow_manager.models.analysis_context import AnalysisContext
from workflow_manager.models.library import Library


class AnalysisRunManager(OrcaBusBaseManager):
    pass


class AnalysisRun(OrcaBusBaseModel):
    orcabus_id = OrcabusIdField(prefix='anr', primary_key=True)

    analysis_run_id = models.CharField(max_length=255, unique=True)

    analysis_run_name = models.CharField(max_length=255)
    comment = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)

    approval_context = models.ForeignKey(AnalysisContext, null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name="approval_context")
    project_context = models.ForeignKey(AnalysisContext, null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name="project_context")
    analysis = models.ForeignKey(Analysis, null=True, blank=True, on_delete=models.SET_NULL)
    libraries = models.ManyToManyField(Library)

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
