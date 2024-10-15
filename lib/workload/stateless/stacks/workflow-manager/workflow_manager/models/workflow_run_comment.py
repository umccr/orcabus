from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.workflow_run import WorkflowRun


class WorkflowRunCommentManager(OrcaBusBaseManager):
    pass


class WorkflowRunComment(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    workflow_run = models.ForeignKey(WorkflowRun, related_name='comments', on_delete=models.CASCADE)
    comment = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255) # FIXME: change to user, currently using email
    is_deleted = models.BooleanField(default=False)

    objects = WorkflowRunCommentManager()

    def __str__(self):
        return f"ID: {self.id}, comment: {self.comment}, created_by: {self.created_by}, created_at: {self.created_at}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "comment": self.comment,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_deleted": self.is_deleted
        }
    