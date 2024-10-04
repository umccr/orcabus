from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class WorkflowManager(OrcaBusBaseManager):
    pass


class Workflow(OrcaBusBaseModel):
    class Meta:
        # a combo of this gives us human-readable pipeline id
        unique_together = ["workflow_name", "workflow_version"]

    orcabus_id_prefix = 'wfl.'

    workflow_name = models.CharField(max_length=255)
    workflow_version = models.CharField(max_length=255)
    execution_engine = models.CharField(max_length=255)

    # definition from an external system (as known to the execution engine)
    execution_engine_pipeline_id = models.CharField(max_length=255)

    # approval_state = models.CharField(max_length=255)  # FIXME: Do we still need this (or just use Analysis)?

    objects = WorkflowManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, workflow_name: {self.workflow_name}, workflow_version: {self.workflow_version}"
    
    def to_dict(self):
        return {
            "orcabusId": self.orcabus_id,
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "execution_engine": self.execution_engine,
            "execution_engine_pipeline_id": self.execution_engine_pipeline_id,
            # "approval_state": self.approval_state
        }
