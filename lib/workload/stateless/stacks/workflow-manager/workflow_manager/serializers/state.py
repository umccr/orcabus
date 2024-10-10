from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import State, WorkflowRun, Payload


class StateBaseSerializer(SerializersBase):
    prefix = State.orcabus_id_prefix


class StateMinSerializer(StateBaseSerializer):
    class Meta:
        model = State
        fields = ["orcabus_id", "status"]


class StateSerializer(StateBaseSerializer):
    class Meta:
        model = State
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['workflow_run'] = WorkflowRun.orcabus_id_prefix + representation['workflow_run']
        if representation['payload']:
            representation['payload'] = Payload.orcabus_id_prefix + representation['payload']
        return representation
