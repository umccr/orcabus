from rest_framework import serializers

from sequence_run_manager.models import State, Sequence
from sequence_run_manager.serializers.base import SerializersBase, OptionalFieldsMixin, OrcabusIdSerializerMetaMixin


class StateBaseSerializer(SerializersBase):
    pass


class StateSerializer(StateBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = State
        fields = "__all__"
