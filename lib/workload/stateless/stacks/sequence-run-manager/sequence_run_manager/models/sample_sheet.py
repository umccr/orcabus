from django.db import models

from sequence_run_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager
from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.fields import OrcaBusIdField


class SampleSheetManager(OrcaBusBaseManager):
    pass


class SampleSheet(OrcaBusBaseModel):
    orcabus_id = OrcaBusIdField(primary_key=True, prefix='ss')
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
    sample_sheet_name = models.CharField(max_length=255, null=False, blank=False)
    association_status = models.CharField(max_length=255, null=False, blank=False, default='active')
    association_timestamp = models.DateTimeField(auto_now_add=True)
    
    # JSONB field
    sample_sheet_content = models.JSONField()
    
    # TODO: add checksums field and filemanager orcabus_id if needed
    # checksums = models.JSONField()
    # fm_orcabus_id = OrcaBusIdField(prefix='fm')

    objects = SampleSheetManager()
    
    def __str__(self):
        return f"ID: {self.orcabus_id}, sample_sheet_name: {self.sample_sheet_name}, sequence: {self.sequence}"