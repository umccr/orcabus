from rest_framework import serializers

from sequence_run_manager.models import State, Sequence
from sequence_run_manager.serializers.base import SerializersBase, OptionalFieldsMixin


class StateBaseSerializer(SerializersBase):
    pass


class StateSerializer(StateBaseSerializer):
    class Meta:
        model = State
        fields = "__all__"
