from django.db import models

from workflow_manager.models.analysis_run import AnalysisRun
from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.library import Library
from workflow_manager.models.workflow import Workflow


class WorkflowRunManager(OrcaBusBaseManager):
    pass


class WorkflowRun(OrcaBusBaseModel):
    orcabus_id_prefix = 'wfr.'

    portal_run_id = models.CharField(max_length=255, unique=True)

    execution_id = models.CharField(max_length=255, null=True, blank=True)
    workflow_run_name = models.CharField(max_length=255, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)

    # Relationships
    workflow = models.ForeignKey(Workflow, null=True, blank=True, on_delete=models.SET_NULL)
    analysis_run = models.ForeignKey(AnalysisRun, null=True, blank=True, on_delete=models.SET_NULL)
    libraries = models.ManyToManyField(Library, through="LibraryAssociation")

    objects = WorkflowRunManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, portal_run_id: {self.portal_run_id}, workflow_run_name: {self.workflow_run_name}, " \
               f"workflowRun: {self.workflow.workflow_name} "

    def to_dict(self):
        return {
            "orcabusId": self.orcabus_id,
            "portal_run_id": self.portal_run_id,
            "execution_id": self.execution_id,
            "workflow_run_name": self.workflow_run_name,
            "comment": self.comment,
            "workflow": self.workflow.to_dict() if (self.workflow is not None) else None
        }

    def get_all_states(self):
        # retrieve all states (DB records rather than a queryset)
        return list(self.state_set.all())  # TODO: ensure order by timestamp ?


class LibraryAssociationManager(OrcaBusBaseManager):
    pass


class LibraryAssociation(OrcaBusBaseModel):
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.CASCADE)
    association_date = models.DateTimeField()
    status = models.CharField(max_length=255)

    objects = LibraryAssociationManager()
