from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.payload import Payload
from workflow_manager.models.workflow import Workflow
from workflow_manager.models.library import Library


class WorkflowRunManager(OrcaBusBaseManager):
    pass


class WorkflowRun(OrcaBusBaseModel):
    class Meta:
        unique_together = ["portal_run_id", "status", "timestamp"]

    id = models.BigAutoField(primary_key=True)

    # --- mandatory fields

    portal_run_id = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    # --- optional fields

    # ID of the external service
    execution_id = models.CharField(max_length=255, null=True, blank=True)
    workflow_run_name = models.CharField(max_length=255, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)

    # --- FK link to value objects

    # Link to workflow table
    workflow = models.ForeignKey(Workflow, null=True, blank=True, on_delete=models.SET_NULL)

    # Link to workflow payload data
    payload = models.ForeignKey(Payload, null=True, blank=True, on_delete=models.SET_NULL)

    # Link to library table
    libraries = models.ManyToManyField(Library, through="LibraryAssociation")


    objects = WorkflowRunManager()

    def __str__(self):
        return f"ID: {self.id}, portal_run_id: {self.portal_run_id}"

    def to_dict(self):
        return {
            "id": self.id,
            "portal_run_id": self.portal_run_id,
            "status": self.status,
            "timestamp": str(self.timestamp),
            "execution_id": self.execution_id,
            "workflow_run_name": self.workflow_run_name,
            "comment": self.comment,
            "payload": self.payload.to_dict() if (self.payload is not None) else None,
            "workflow": self.workflow.to_dict() if (self.workflow is not None) else None
        }


class LibraryAssociation(OrcaBusBaseModel):
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.CASCADE)
    association_date = models.DateTimeField()
    status = models.CharField(max_length=255)
