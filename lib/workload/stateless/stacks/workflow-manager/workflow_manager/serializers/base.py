from rest_framework import serializers


class SerializersBase(serializers.ModelSerializer):
    prefix = ''

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['orcabus_id'] = self.prefix + str(representation['orcabus_id'])
        return representation

class OptionalFieldsMixin:
    def make_fields_optional(self):
        # Get the list of fields to exclude
        
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
