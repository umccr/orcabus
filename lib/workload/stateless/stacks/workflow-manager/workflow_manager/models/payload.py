from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class PayloadManager(OrcaBusBaseManager):
    pass


class Payload(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    # Definition from an external source (as known to the execution engine)
    payload_type = models.CharField(max_length=255)
    payload_ref_id = models.CharField(max_length=255, unique=True)
    data = models.JSONField(encoder=DjangoJSONEncoder)

    objects = PayloadManager()

    def __str__(self):
        return f"ID: {self.id}, payload_ref_id: {self.payload_ref_id}"
