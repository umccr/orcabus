from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import Workflow


class WorkflowBaseSerializer(SerializersBase):
    prefix = Workflow.orcabus_id_prefix


class WorkflowMinSerializer(WorkflowBaseSerializer):
    class Meta:
        model = Workflow
        fields = ["orcabus_id", "workflow_name"]


class WorkflowSerializer(WorkflowBaseSerializer):
    class Meta:
        model = Workflow
        fields = "__all__"
