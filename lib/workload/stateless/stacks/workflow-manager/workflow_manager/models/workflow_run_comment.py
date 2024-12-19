from django.db import models

from workflow_manager.fields import OrcaBusIdField
from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.workflow_run import WorkflowRun


class WorkflowRunCommentManager(OrcaBusBaseManager):
    pass


class WorkflowRunComment(OrcaBusBaseModel):

    orcabus_id = OrcaBusIdField(primary_key=True, prefix='cmt')
    workflow_run = models.ForeignKey(WorkflowRun, related_name="comments", on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = WorkflowRunCommentManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, workflow_run: {self.workflow_run}, comment: {self.comment}"
