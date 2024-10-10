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
from app.pagination import PaginationConstant

logger = logging.getLogger(__name__)


class BaseManager(models.Manager):
    def get_by_keyword(self, qs=None, **kwargs) -> QuerySet:
        if qs is None:
            qs = super().get_queryset()
        return self.get_model_fields_query(qs, **kwargs)

    @staticmethod
    def reduce_multi_values_qor(key: str, values: List[str]):
        if not isinstance(
                values,
                list,
        ):
            values = [values]
        return reduce(
            operator.or_, (Q(**{"%s__iexact" % key: value})
                           for value in values)
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

    def update_or_create_if_needed(self, search_key: dict, data: dict) -> tuple[models.Model, bool, bool]:
        """
        The regular django update_or_create method will always update the record even if there is no change. This
        method is a wrapper that will check and only update or create when necessary.

        Args:
            search_key (dict): The search key to find the object
            data (dict): The latest data to update or create if needed

        Returns:
            tuple: A tuple containing:
                - obj (Model): The object that is updated or created
                - is_created (bool): A boolean if the object is created
                - is_updated (bool): A boolean if the object is updated
        """

        try:
            # We wanted the exact match of the data, else we need to update this
            obj = self.get(**data)
            return obj, False, False
        except self.model.DoesNotExist:
            # If the search key doesn't exist it will create a new one, else it will update the record no matter what
            obj, is_created = self.update_or_create(**search_key, defaults=data)

            # obj, is_created, is_updated (if the object is created, it is not updated)
            return obj, is_created, not is_created


class BaseModel(models.Model):
    class Meta:
        abstract = True

    orcabus_id = models.CharField(
        primary_key=True,
        unique=True,
        editable=False,
        blank=False,
        null=False,
        validators=[
            RegexValidator(
                regex=r'[\w]{26}$',
                message='ULID is expected to be 26 characters long',
                code='invalid_orcabus_id'
            )]

    )

    def save(self, *args, **kwargs):
        if not self.orcabus_id:
            self.orcabus_id = ulid.new().str
        self.full_clean()

        return super(BaseModel, self).save(*args, **kwargs)

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
