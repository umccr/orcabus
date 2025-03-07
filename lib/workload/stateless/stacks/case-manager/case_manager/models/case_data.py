from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from case_manager.fields import OrcaBusIdField
from case_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class CaseDataManager(OrcaBusBaseManager):
    pass


class CaseData(OrcaBusBaseModel):
    orcabus_id = OrcaBusIdField(primary_key=True, prefix='cdata')
    data = models.JSONField(encoder=DjangoJSONEncoder)

    objects = CaseDataManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}"
