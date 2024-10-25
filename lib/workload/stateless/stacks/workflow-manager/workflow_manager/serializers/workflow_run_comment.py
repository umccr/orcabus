from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import WorkflowRunComment, WorkflowRun

class WorkflowRunCommentBaseSerializer(SerializersBase):
    prefix = WorkflowRunComment.orcabus_id_prefix
    
class WorkflowRunCommentMinSerializer(WorkflowRunCommentBaseSerializer):
    class Meta:
        model = WorkflowRunComment
        fields = ["orcabus_id", "comment", "timestamp"]

class WorkflowRunCommentSerializer(WorkflowRunCommentBaseSerializer):
    class Meta:
        model = WorkflowRunComment
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['workflow_run'] = WorkflowRun.orcabus_id_prefix + representation['workflow_run']
        return representation