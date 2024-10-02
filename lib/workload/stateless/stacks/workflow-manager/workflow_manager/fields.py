import hashlib
import ulid

from django.db import models
from django.core.validators import RegexValidator

orcabus_id_validator = RegexValidator(
                regex=r'[\w]{26}$',
                message='ULID is expected to be 26 characters long',
                code='invalid_orcabus_id'
            )


class OrcabusIdField(models.CharField):
    description = "An OrcaBus internal ID (ULID)"

    def __init__(self, prefix, *args, **kwargs):
        kwargs["max_length"] = 26  # ULID length
        kwargs['unique'] = True
        kwargs['editable'] = False
        kwargs['blank'] = False
        kwargs['null'] = False
        kwargs['default'] = ulid.new
        kwargs['validators'] = [orcabus_id_validator]
        super().__init__(*args, **kwargs)


class HashField(models.CharField):
    description = (
        "HashField is related to some base fields (other columns) in a model and"
        "stores its hashed value for better indexing performance."
    )

    def __init__(self, base_fields, *args, **kwargs):
        """
        :param base_fields: name of fields storing the value to be hashed
        """
        self.base_fields = base_fields
        kwargs["max_length"] = 64
        super(HashField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        if self.base_fields is not None:
            kwargs["base_fields"] = self.base_fields
        return name, path, args, kwargs

    def pre_save(self, instance, add):
        self.calculate_hash(instance)
        return super(HashField, self).pre_save(instance, add)

    def calculate_hash(self, instance):
        sha256 = hashlib.sha256()
        for field in self.base_fields:
            value = getattr(instance, field)
            sha256.update(value.encode("utf-8"))
        setattr(instance, self.attname, sha256.hexdigest())


class HashFieldHelper(object):
    def __init__(self):
        self.__sha256 = hashlib.sha256()

    def add(self, value):
        self.__sha256.update(value.encode("utf-8"))
        return self

    def calculate_hash(self):
        return self.__sha256.hexdigest()
