import re
from rest_framework import serializers


def to_camel_case(snake_str):
    components = re.split(r'[_\-\s]', snake_str)
    return components[0].lower() + ''.join(x.title() for x in components[1:])


class SerializersBase(serializers.ModelSerializer):
    prefix = ''

    def __init__(self, *args, camel_case_data=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_camel_case = camel_case_data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['orcabus_id'] = self.prefix + str(representation['orcabus_id'])

        if self.use_camel_case:
            return {to_camel_case(key): value for key, value in representation.items()}
        return representation


class OptionalFieldsMixin:
    def make_fields_optional(self):
        # Make all fields optional
        for field in self.fields.values():
            field.required = False

        # If the fields are CharField, you might also want to allow them to be blank
        for field_name, field in self.fields.items():
            if isinstance(field, serializers.CharField):
                field.allow_blank = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_fields_optional()