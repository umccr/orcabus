from django.db import models

from fastq_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class FastqPairManager(OrcaBusBaseManager):
    pass


class FastqPair(OrcaBusBaseModel):
    id = models.BigAutoField(primary_key=True)

    rgid = models.CharField(max_length=255, null=True, blank=True)
    rgsm = models.CharField(max_length=255, null=True, blank=True)
    rglb = models.CharField(max_length=255, null=True, blank=True)

    coverage = models.CharField(max_length=255, null=True, blank=True)
    quality = models.CharField(max_length=255, null=True, blank=True)
    is_archived = models.BooleanField(null=True, blank=True)
    is_compressed = models.BooleanField(null=True, blank=True)

    read_1_id = models.CharField(max_length=255, null=True, blank=True)
    read_2_id = models.CharField(max_length=255, null=True, blank=True)

    objects = FastqPairManager()

    def __str__(self):
        return f"ID: {self.id}, rgid: {self.rgid}"
