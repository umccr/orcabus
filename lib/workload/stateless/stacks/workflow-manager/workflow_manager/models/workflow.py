from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class WorkflowManager(OrcaBusBaseManager):
    pass


class Workflow(OrcaBusBaseModel):
    class Meta:
        # a combo of this gives us human-readable pipeline id
        unique_together = ["workflow_name", "workflow_version"]

    id = models.BigAutoField(primary_key=True)

    # human choice - how this is being named
    workflow_name = models.CharField(max_length=255)

    # human choice - how this is being named
    workflow_version = models.CharField(max_length=255)

    # human choice - how this is being named
    execution_engine = models.CharField(max_length=255)

    # definition from an external system (as known to the execution engine)
    execution_engine_pipeline_id = models.CharField(max_length=255)

    approval_state = models.CharField(max_length=255)  # FIXME: figure out what states we have and how many

    objects = WorkflowManager()

    def __str__(self):
        return f"ID: {self.id}, workflow_name: {self.workflow_name}, workflow_version: {self.workflow_version}"
