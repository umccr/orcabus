from sequence_run_manager.models import State
from sequence_run_manager.serializers.base import SerializersBase, OrcabusIdSerializerMetaMixin


class StateBaseSerializer(SerializersBase):
    pass

class StateSerializer(StateBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = State
        fields = "__all__"
