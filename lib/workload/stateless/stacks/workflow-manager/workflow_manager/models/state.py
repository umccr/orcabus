from enum import Enum
from typing import List

from django.db import models

from workflow_manager.fields import OrcaBusIdField
from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.payload import Payload
from workflow_manager.models.workflow_run import WorkflowRun


class Status(Enum):
    DRAFT = "DRAFT", ['DRAFT', 'INITIAL', 'CREATED']
    READY = "READY", ['READY']
    RUNNING = "RUNNING", ['RUNNING', 'IN_PROGRESS']
    SUCCEEDED = "SUCCEEDED", ['SUCCEEDED', 'SUCCESS']
    FAILED = "FAILED", ['FAILED', 'FAILURE', 'FAIL']
    ABORTED = "ABORTED", ['ABORTED', 'CANCELLED', 'CANCELED']
    RESOLVED = "RESOLVED", ['RESOLVED']

    def __init__(self, convention: str, aliases: List[str]):
        self.convention = convention
        self.aliases = aliases

    def __str__(self):
        return self.convention

    @staticmethod
    def get_convention(status: str):
        # enforce upper case convention
        status = status.upper()
        status = status.replace("-", "_")
        # TODO: handle other characters?
        for s in Status:
            if status in s.aliases:
                return s.convention

        # retain all uncontrolled states
        return status

    @staticmethod
    def is_supported(status: str) -> bool:
        # enforce upper case convention
        status = status.upper()
        for s in Status:
            if status in s.aliases:
                return True
        return False

    @staticmethod
    def is_terminal(status: str) -> bool:
        # enforce upper case convention
        status = status.upper()
        for s in [Status.SUCCEEDED, Status.FAILED, Status.ABORTED]:
            if status in s.aliases:
                return True
        return False

    @staticmethod
    def is_draft(status: str) -> bool:
        # enforce upper case convention
        status = status.upper()
        return status in Status.DRAFT.aliases

    @staticmethod
    def is_running(status: str) -> bool:
        # enforce upper case convention
        status = status.upper()
        return status in Status.RUNNING.aliases

    @staticmethod
    def is_ready(status: str) -> bool:
        # enforce upper case convention
        status = status.upper()
        return status in Status.READY.aliases

    @staticmethod
    def is_resolved(status: str) -> bool:
        # enforce upper case convention
        status = status.upper()
        return status in Status.RESOLVED.aliases


class StateManager(OrcaBusBaseManager):
    pass


class State(OrcaBusBaseModel):
    class Meta:
        unique_together = ["workflow_run", "status", "timestamp"]

    # --- mandatory fields
    orcabus_id = OrcaBusIdField(primary_key=True, prefix='stt')
    status = models.CharField(max_length=255)  # TODO: How and where to enforce conventions?
    timestamp = models.DateTimeField()
    comment = models.CharField(max_length=255, null=True, blank=True)

    workflow_run = models.ForeignKey(WorkflowRun, related_name='states', on_delete=models.CASCADE)
    # Link to workflow run payload data
    payload = models.ForeignKey(Payload, null=True, blank=True, on_delete=models.SET_NULL)

    objects = StateManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, status: {self.status}"

    def is_terminal(self) -> bool:
        return Status.is_terminal(str(self.status))

    def is_draft(self) -> bool:
        return Status.is_draft(str(self.status))

    def is_ready(self) -> bool:
        return Status.is_ready(str(self.status))

    def is_running(self) -> bool:
        return Status.is_running(str(self.status))
