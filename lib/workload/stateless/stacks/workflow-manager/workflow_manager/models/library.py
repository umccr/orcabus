from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from workflow_manager.models.workflow import Workflow


class LibraryManager(OrcaBusBaseManager):
    pass


class Library(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    library_id = models.CharField(max_length=255, unique=True)

    objects = LibraryManager()

    def __str__(self):
        return f"ID: {self.id}, library_id: {self.library_id}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "library_id": self.library_id
        }
