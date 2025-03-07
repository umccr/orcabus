from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from case_manager.fields import OrcaBusIdField
from case_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class LibraryManager(OrcaBusBaseManager):
    pass


class Library(OrcaBusBaseModel):

    orcabus_id = OrcaBusIdField(primary_key=True, prefix='clib')

    library_id = models.CharField(max_length=255)

    objects = LibraryManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, library_id: {self.library_id}"
