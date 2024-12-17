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

from simple_history.models import HistoricalRecords

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
            # Apparently the `get_prep_value` from the custom fields.py is not called prior hitting the Db but,
            # the regular `__exact` still execute that function.
            operator.or_, (Q(**{"%s__exact" % key: value})
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
                print('query_string', query_string)
                qs = qs.filter(query_string)
        except FieldError as e:
            logger.debug(e)
            qs = qs.none()

        return qs

    def update_or_create_if_needed(self, search_key: dict, data: dict, user_id: str = None,
                                   change_reason: str = None) -> tuple[models.Model, bool, bool]:
        """
        The regular Django `update_or_create` method will always update the record even if there is no change. This
        method will only update the record if there is a change. It also includes extra functionality to record the
        user and change reason in the history tables as part of the audit.

        Args:
            search_key (dict): The search key to find the object.
            data (dict): The latest data to update or create if needed.
            user_id (str): The ID of the user making the change (could potentially be the email address).
            change_reason (str): The reason for the change/insert.

        Returns:
            tuple: A tuple containing:
                - obj (Model): The object that is updated or created
                - is_created (bool): A boolean if the object is created
                - is_updated (bool): A boolean if the object is updated
        """
        is_created = False
        is_updated = False
        try:
            obj = self.get(**search_key)
            for key, value in data.items():
                # compare both value in str format to avoid any type mismatch
                if str(getattr(obj, key)) != str(value):
                    setattr(obj, key, value)
                    is_updated = True
        except self.model.DoesNotExist:
            obj = self.model(**data)
            is_created = True
        if is_created or is_updated:
            obj._history_user = user_id
            obj._change_reason = change_reason
            obj.save()

        return obj, is_created, is_updated


class BaseModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # To make django validate the constraint before saving it
        self.full_clean()

        super(BaseModel, self).save(*args, **kwargs)

        # Reload the object from the database to ensure custom fields like OrcaBusIdField
        # invoke the `from_db_value` method (which provides the annotation) after saving.
        self.refresh_from_db()


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


class BaseHistoricalRecords(HistoricalRecords):
    """
    This should alter user_id tracking to models.CharField instead of user model
    """

    def _history_user_setter(self, historical_instance, user_id):
        historical_instance.history_user_id = user_id

    def __init__(self, *args, **kwargs):
        super().__init__(
            history_user_id_field=models.CharField(null=True, blank=True),
            history_user_setter=self._history_user_setter,
            *args, **kwargs
        )
