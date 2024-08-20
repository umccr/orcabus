from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models import WorkflowRun, Payload


class StateManager(OrcaBusBaseManager):
    pass


class State(OrcaBusBaseModel):
    class Meta:
        unique_together = ["workflow_run", "status", "timestamp"]

    id = models.BigAutoField(primary_key=True)

    # --- mandatory fields
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    comment = models.CharField(max_length=255, null=True, blank=True)

    # Link to workflow run payload data
    payload = models.ForeignKey(Payload, null=True, blank=True, on_delete=models.SET_NULL)

    objects = StateManager()

    def __str__(self):
        return f"ID: {self.id}, status: {self.status}"

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_run_id": self.workflow_run.id,
            "status": self.status,
            "timestamp": str(self.timestamp),
            "comment": self.comment,
            "payload": self.payload.to_dict() if (self.payload is not None) else None,
        }

