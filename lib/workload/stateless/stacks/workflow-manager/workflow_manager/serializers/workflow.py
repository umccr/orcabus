from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from workflow_manager.models import Workflow


class WorkflowBaseSerializer(SerializersBase):
    prefix = Workflow.orcabus_id_prefix

class WorkflowListParamSerializer(OptionalFieldsMixin, WorkflowBaseSerializer):
    class Meta:
        model = Workflow
        fields = "__all__"

class WorkflowMinSerializer(WorkflowBaseSerializer):
    class Meta:
        model = Workflow
        fields = ["orcabus_id", "workflow_name", "workflow_version"]


class WorkflowSerializer(WorkflowBaseSerializer):
    class Meta:
        model = Workflow
        fields = "__all__"
