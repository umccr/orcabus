import logging
import operator
import ulid
from functools import reduce
from typing import List

from django.core.exceptions import FieldError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import (
    Q,
    ManyToManyField,
    ForeignKey,
    ForeignObject,
    OneToOneField,
    ForeignObjectRel,
    ManyToOneRel,
    ManyToManyRel,
    OneToOneRel,
    QuerySet,
)
from rest_framework.settings import api_settings

from sequence_run_manager.pagination import PaginationConstant

logger = logging.getLogger(__name__)

orcabus_id_validator = RegexValidator(
                regex=r'^[\w]{26}$',
                message='ULID is expected to be 26 characters long',
                code='invalid_orcabus_id'
            )


class OrcaBusBaseManager(models.Manager):
    @staticmethod
    def reduce_multi_values_qor(key: str, values: List[str]):
        if isinstance(
            values,
            (
                str,
                int,
                float,
            ),
        ):
            values = [values]
        return reduce(
            operator.or_, (Q(**{"%s__iexact" % key: value}) for value in values)
        )

    def get_model_fields_query(self, qs: QuerySet, **kwargs) -> QuerySet:
        def exclude_params(params):
            for param in params:
                kwargs.pop(param) if param in kwargs.keys() else None

        exclude_params(
            [
                api_settings.SEARCH_PARAM,
                api_settings.ORDERING_PARAM,
                PaginationConstant.PAGE,
                PaginationConstant.ROWS_PER_PAGE,
                "sortCol",
                "sortAsc",
            ]
        )

        query_string = None

        for key, values in kwargs.items():
            each_query = self.reduce_multi_values_qor(key, values)
            if query_string:
                query_string = query_string & each_query
            else:
                query_string = each_query

        try:
            if query_string:
                qs = qs.filter(query_string)
        except FieldError as e:
            logger.debug(e)
            qs = qs.none()

        return qs


class OrcaBusBaseModel(models.Model):
    class Meta:
        abstract = True
        
    orcabus_id_prefix = None

    orcabus_id = models.CharField(
        primary_key=True,
        unique=True,
        editable=False,
        blank=False,
        null=False,
        validators=[orcabus_id_validator]
    )
    
    def save(self, *args, **kwargs):
        # handle the OrcaBus ID
        if not self.orcabus_id:
            # if no OrcaBus ID was provided, then generate one
            self.orcabus_id = ulid.new().str
        else:
            # check provided OrcaBus ID
            if len(self.orcabus_id) > 26:
                # assume the OrcaBus ID carries the prefix
                # we strip it off and continue to the validation
                l = len(self.orcabus_id_prefix)
                self.orcabus_id = str(self.orcabus_id)[l:]
        self.full_clean()  # make sure we are validating the inputs (especially the OrcaBus ID)
        return super(OrcaBusBaseModel, self).save(*args, **kwargs)

    @classmethod
    def get_fields(cls):
        return [f.name for f in cls._meta.get_fields()]

    @classmethod
    def get_base_fields(cls):
        base_fields = set()
        for f in cls._meta.get_fields():
            if isinstance(
                f,
                (
                    ForeignKey,
                    ForeignObject,
                    OneToOneField,
                    ManyToManyField,
                    ForeignObjectRel,
                    ManyToOneRel,
                    ManyToManyRel,
                    OneToOneRel,
                ),
            ):
                continue
            base_fields.add(f.name)
        return list(base_fields)
