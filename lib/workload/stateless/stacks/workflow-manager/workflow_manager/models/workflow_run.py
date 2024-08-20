from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models import Workflow, Library, State


class WorkflowRunManager(OrcaBusBaseManager):
    pass


class WorkflowRun(OrcaBusBaseModel):

    id = models.BigAutoField(primary_key=True)

    # --- mandatory fields

    portal_run_id = models.CharField(max_length=255, unique=True)
    current_status = models.CharField(max_length=255)
    created = models.DateTimeField()
    last_modified = models.DateTimeField()

    # --- optional fields

    # ID of the external service
    execution_id = models.CharField(max_length=255, null=True, blank=True)
    workflow_run_name = models.CharField(max_length=255, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)

    # --- FK link to value objects

    # Link to workflow table
    workflow = models.ForeignKey(Workflow, null=True, blank=True, on_delete=models.SET_NULL)

    # Link to library table
    libraries = models.ManyToManyField(Library, through="LibraryAssociation")

    objects = WorkflowRunManager()

    def __str__(self):
        return f"ID: {self.id}, portal_run_id: {self.portal_run_id}"

    def to_dict(self):
        return {
            "id": self.id,
            "portal_run_id": self.portal_run_id,
            "current_status": self.current_status,
            "created": str(self.created),
            "last_modified": str(self.last_modified),
            "execution_id": self.execution_id,
            "workflow_run_name": self.workflow_run_name,
            "comment": self.comment,
            "workflow": self.workflow.to_dict() if (self.workflow is not None) else None
        }


class LibraryAssociationManager(OrcaBusBaseManager):
    pass


class LibraryAssociation(OrcaBusBaseModel):
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.CASCADE)
    association_date = models.DateTimeField()
    status = models.CharField(max_length=255)

    objects = LibraryAssociationManager()
