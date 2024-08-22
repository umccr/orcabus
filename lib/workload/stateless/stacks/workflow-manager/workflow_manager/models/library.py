from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class LibraryManager(OrcaBusBaseManager):
    pass


class Library(OrcaBusBaseModel):

    orcabus_id = models.CharField(primary_key=True, max_length=255)
    library_id = models.CharField(max_length=255)

    objects = LibraryManager()

    def __str__(self):
        return f"orcabus_id: {self.orcabus_id}, library_id: {self.library_id}"
    
    def to_dict(self):
        return {
            "orcabus_id": self.orcabus_id,
            "library_id": self.library_id
        }
