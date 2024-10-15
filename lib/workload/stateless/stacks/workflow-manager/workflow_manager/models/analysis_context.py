from django.db import models

from enum import Enum
from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class AnalysisContextOption(Enum):
    """
    Supported / expected values for an AnalysisContext.
    # TODO: replace with more controlled / formalised models.TextChoices?
    """
    NATA = "NATA"
    CLINICAL = "clinical"
    RESEARCH = "research"
    INTERNAL = "internal"
    VALIDATION = "validation"
    DEVELOPMENT = "development"

class AnalysisContextUsecase(Enum):
    """
    Supported / expected values for an AnalysisContext.
    # TODO: replace with more controlled / formalised models.TextChoices?
    """
    ANALYSIS = "analysis"
    STORAGE = "storage"
    COMPUTE_ENV = "compute-env"

class AnalysisContextManager(OrcaBusBaseManager):
    pass


class AnalysisContext(OrcaBusBaseModel):
    class Meta:
        unique_together = ["name", "usecase"]

    orcabus_id_prefix = 'ctx.'

    name = models.CharField(max_length=255)  # Supposed to be the value of an AnalysisContextOption
    usecase = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=255)

    objects = AnalysisContextManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, name: {self.name}, usecase: {self.usecase}"
