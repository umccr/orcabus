import logging

from django.db import models
from django.db.models import QuerySet

from app.models import Library
from app.models.base import BaseModel, BaseManager


class LibraryRunManager(BaseManager):
    None


# Disabled
# Uncomment from ../__init__.py to enable

class LibraryRun(BaseModel):
    objects = LibraryRunManager()

    # Possible to have its own model of sequence_run
    sequence_run_id = models.CharField(
        blank=True,
        null=True
    )

    lane = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )
    override_cycles = models.CharField(
        blank=True,
        null=True
    )
    coverage_yield = models.CharField(
        blank=True,
        null=True
    )
    qc_status = models.CharField(
        blank=True,
        null=True
    )

    library = models.ForeignKey(Library, on_delete=models.SET_NULL, null=True, blank=False)
