from django.db import models

from enum import Enum
from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class ApprovalOption(Enum):
    """
    Supported / expected values for a approval AnalysisContext.
    """
    NATA = "NATA"
    CLINICAL = "clinical"

class ComputeOption(Enum):
    """
    Supported / expected values for a compute env AnalysisContext.
    """
    ACCREDITED = "accredited"
    RESEARCH = "research"

class StorageOption(Enum):
    """
    Supported / expected values for a storage AnalysisContext.
    """
    ACCREDITED = "accredited"
    RESEARCH = "research"
    TEMP = "temp"

class Usecase(Enum):
    """
    Supported / expected values for an AnalysisContext.
    """
    APPROVAL = "approval"
    STORAGE = "storage"
    COMPUTE = "compute"

class AnalysisContextManager(OrcaBusBaseManager):
    pass


class AnalysisContext(OrcaBusBaseModel):
    class Meta:
        unique_together = ["name", "usecase"]

    orcabus_id_prefix = 'ctx.'

    name = models.CharField(max_length=255)  # Supposed to be the value of an AnalysisContextOption
    usecase = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)

    objects = AnalysisContextManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, name: {self.name}, usecase: {self.usecase}"
