from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from workflow_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class PayloadManager(OrcaBusBaseManager):
    pass


class Payload(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    payload_ref_id = models.CharField(max_length=255, unique=True)
    version = models.CharField(max_length=255)
    data = models.JSONField(encoder=DjangoJSONEncoder)

    objects = PayloadManager()

    def __str__(self):
        return f"ID: {self.id}, payload_ref_id: {self.payload_ref_id}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "payload_ref_id": self.payload_ref_id,
            "version": self.version,
            "data": self.data
        }
