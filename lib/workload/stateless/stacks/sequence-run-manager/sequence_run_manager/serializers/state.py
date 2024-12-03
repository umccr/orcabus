from rest_framework import serializers

from sequence_run_manager.models import State
from sequence_run_manager.serializers.base import SerializersBase, OptionalFieldsMixin

class StateBaseSerializer(SerializersBase):
    orcabus_id_prefix = State.orcabus_id_prefix

class StateSerializer(StateBaseSerializer):
    class Meta:
        model = State
        fields = "__all__"
