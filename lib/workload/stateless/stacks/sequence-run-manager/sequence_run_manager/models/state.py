from django.db import models

from sequence_run_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.fields import OrcaBusIdField


class StateManager(OrcaBusBaseManager):
    pass


class State(OrcaBusBaseModel):
    orcabus_id = OrcaBusIdField(primary_key=True, prefix='sqs')

    status = models.CharField(max_length=255, null=False, blank=False)
    timestamp = models.DateTimeField()
    comment = models.CharField(max_length=255, null=True, blank=True)

    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name='states')

    objects = StateManager()

    def __str__(self):
        return f"ID: {self.orcabus_id}, status: {self.status}, for {self.sequence}"
