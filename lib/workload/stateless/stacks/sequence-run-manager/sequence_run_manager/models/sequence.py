import logging

from django.db import models
from django.db.models import QuerySet

from sequence_run_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager

logger = logging.getLogger(__name__)


class SequenceStatus(models.TextChoices):
    # Convention: status values are to be stored as upper cases
    STARTED = "STARTED"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    ABORTED = "ABORTED"

    @classmethod
    def from_value(cls, value):
        if value == cls.STARTED.value:
            return cls.STARTED
        elif value == cls.SUCCEEDED.value:
            return cls.SUCCEEDED
        elif value == cls.FAILED.value:
            return cls.FAILED
        else:
            raise ValueError(f"No matching SequenceStatus found for value: {value}")

    @classmethod
    def from_seq_run_status(cls, value):
        """
        See Run Status
        https://support.illumina.com/help/BaseSpace_Sequence_Hub/Source/Informatics/BS/Statuses_swBS.htm

        Note that we don't necessary support all these statuses. In the following check, those values come
        from observed values from our BSSH run events.

        See https://github.com/umccr-illumina/stratus/issues/95

        :param value:
        :return:
        """
        value = str(value).lower()
        if value in ["uploading", "running", "new"]:
            return cls.STARTED
        elif value in ["complete", "analyzing", "pendinganalysis"]:
            return cls.SUCCEEDED
        elif value in ["failed", "needsattention", "timedout", "failedupload"]:
            return cls.FAILED
        elif value in ["stopped"]:
            return cls.ABORTED
        else:
            raise ValueError(f"No matching SequenceStatus found for value: {value}")


class SequenceManager(OrcaBusBaseManager):
    def get_by_keyword(self, **kwargs) -> QuerySet:
        qs: QuerySet = super().get_queryset()
        return self.get_model_fields_query(qs, **kwargs)


class Sequence(OrcaBusBaseModel):
    # primary key
    id = models.BigAutoField(primary_key=True)

    # mandatory non-nullable base fields
    instrument_run_id = models.CharField(
        unique=True, max_length=255, null=False, blank=False
    )  # unique key
    run_volume_name = models.TextField(
        null=False, blank=False
    )  # legacy `gds_volume_name`
    run_folder_path = models.TextField(
        null=False, blank=False
    )  # legacy `gds_folder_path`
    run_data_uri = models.TextField(
        null=False, blank=False
    )  # must be absolute path, including URI scheme/protocol
    status = models.CharField(
        choices=SequenceStatus.choices, max_length=255, null=False, blank=False
    )
    start_time = models.DateTimeField()

    # nullable base fields
    end_time = models.DateTimeField(null=True, blank=True)

    # optional fields -- business look up keys
    reagent_barcode = models.CharField(max_length=255, null=True, blank=True)
    flowcell_barcode = models.CharField(max_length=255, null=True, blank=True)
    sample_sheet_name = models.CharField(max_length=255, null=True, blank=True)
    sequence_run_id = models.CharField(
        max_length=255, null=True, blank=True
    )  # legacy `run_id`
    sequence_run_name = models.CharField(
        max_length=255, null=True, blank=True
    )  # legacy `name`

    # run_config = models.JSONField(null=True, blank=True)  # TODO could be it's own model
    # sample_sheet_config = models.JSONField(null=True, blank=True)  # TODO could be it's own model

    objects = SequenceManager()

    def __str__(self):
        return (
            f"ID '{self.id}', "
            f"Sequence Run ID '{self.sequence_run_id}', "
            f"Sequence Run Name '{self.sequence_run_name}', "
            f"Run Data URI '{self.run_data_uri}', "
            f"Status '{self.status}'"
        )
