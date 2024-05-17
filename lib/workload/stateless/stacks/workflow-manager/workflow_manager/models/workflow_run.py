from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.payload import Payload
from workflow_manager.models.workflow import Workflow


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

    objects = WorkflowRunManager()

    def __str__(self):
        return f"ID: {self.id}, portal_run_id: {self.portal_run_id}"
