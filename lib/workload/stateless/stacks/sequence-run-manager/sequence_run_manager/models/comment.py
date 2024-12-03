import logging

from django.db import models

from sequence_run_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager

logger = logging.getLogger(__name__)

class CommentManager(OrcaBusBaseManager):
    pass


class Comment(OrcaBusBaseModel):
    # primary key
    orcabus_id_prefix = 'cmt.'

    comment = models.TextField(null=False, blank=False)
    association_id = models.CharField(max_length=255, null=False, blank=False) # comment association object id
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = CommentManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, comment: {self.comment}, from {self.created_by}, for {self.association_id}"