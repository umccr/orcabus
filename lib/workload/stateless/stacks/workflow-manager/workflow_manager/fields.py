import ulid
from django.core.validators import RegexValidator
from django.db import models

ULID_REGEX_STR = r"[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}"
ulid_validator = RegexValidator(regex=ULID_REGEX_STR,
                                message='ULID is expected to be 26 characters long',
                                code='invalid_orcabus_id')


def get_ulid() -> str:
    return ulid.new().str


class UlidField(models.CharField):
    description = "An OrcaBus internal ID (ULID)"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 26  # ULID length
        kwargs['validators'] = [ulid_validator]
        kwargs['default'] = get_ulid
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs['validators']
        del kwargs['default']
        return name, path, args, kwargs


class OrcaBusIdField(UlidField):
    description = "An OrcaBus internal ID (based on ULID)"

    def __init__(self, prefix='', *args, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    @property
    def non_db_attrs(self):
        return super().non_db_attrs + ("prefix",)

    def from_db_value(self, value, expression, connection):
        if value and self.prefix != '':
            return f"{self.prefix}.{value}"
        else:
            return value

    def to_python(self, value):
        # This will be called when the function
        return self.get_prep_value(value)

    def get_prep_value(self, value):
        # We just want the last 26 characters which is the ULID (ignoring any prefix) when dealing with the database
        return value[-26:]
