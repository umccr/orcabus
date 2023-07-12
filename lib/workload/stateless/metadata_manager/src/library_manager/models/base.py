import logging
import operator
from functools import reduce
from typing import List

from django.core.exceptions import FieldError
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

from library_manager.pagination import PaginationConstant

logger = logging.getLogger(__name__)


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
