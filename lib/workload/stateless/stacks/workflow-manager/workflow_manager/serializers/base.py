from rest_framework import serializers


class SerializersBase(serializers.ModelSerializer):
    prefix = ''

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['orcabus_id'] = self.prefix + str(representation['orcabus_id'])
        return representation
