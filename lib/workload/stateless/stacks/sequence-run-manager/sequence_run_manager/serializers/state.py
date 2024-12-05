from rest_framework import serializers

from sequence_run_manager.models import State, Sequence
from sequence_run_manager.serializers.base import SerializersBase, OptionalFieldsMixin

class StateBaseSerializer(SerializersBase):
    orcabus_id_prefix = State.orcabus_id_prefix

class StateSerializer(StateBaseSerializer):
    class Meta:
        model = State
        fields = "__all__"
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['sequence'] = Sequence.orcabus_id_prefix + representation['sequence']
        return representation
