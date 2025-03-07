from enum import Enum
from typing import List

from django.db import models

from case_manager.fields import OrcaBusIdField
from case_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from case_manager.models.case import Case



# TODO: this should be a shared lib to enforce convention across services
class Status(Enum):
    DRAFT = "DRAFT", ['DRAFT', 'INITIAL', 'CREATED']
    READY = "READY", ['READY']
    RUNNING = "ONGOING", ['RUNNING', 'IN_PROGRESS', 'ONGOING']
    SUCCEEDED = "SUCCEEDED", ['SUCCEEDED', 'SUCCESS', 'DONE']
    FAILED = "FAILED", ['FAILED', 'FAILURE', 'FAIL', "ERROR"]
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
        unique_together = ["case", "status", "timestamp"]

    orcabus_id = OrcaBusIdField(primary_key=True, prefix='cstt')

    # --- mandatory fields
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    comment = models.CharField(max_length=255, null=True, blank=True)

    case = models.ForeignKey(Case, related_name='states', on_delete=models.CASCADE)

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
