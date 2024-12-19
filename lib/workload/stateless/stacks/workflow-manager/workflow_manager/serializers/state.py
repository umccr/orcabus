from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import State, WorkflowRun, Payload


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
