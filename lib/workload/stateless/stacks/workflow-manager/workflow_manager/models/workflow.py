from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class WorkflowManager(OrcaBusBaseManager):
    pass


class Workflow(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    # Definition from an external source (as known to the execution engine)
    workflow_name = models.CharField(max_length=255)
    workflow_version = models.CharField(max_length=255)
    workflow_ref_id = models.CharField(max_length=255, unique=True)
    execution_engine = models.CharField(max_length=255)

    approval_state = models.CharField(max_length=255) # FIXME: figure out what states we have and how many

    objects = WorkflowManager()

    def __str__(self):
        return f"ID: {self.id}, workflow_ref_id: {self.workflow_ref_id}"
