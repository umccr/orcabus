from case_manager.serializers.base import SerializersBase
from case_manager.models import State, Case, CaseData


class StateBaseSerializer(SerializersBase):
    pass


class StateMinSerializer(StateBaseSerializer):
    class Meta:
        model = State
        fields = ["orcabus_id", "status", "timestamp"]


class StateSerializer(StateBaseSerializer):
    class Meta:
        model = State
        fields = "__all__"
