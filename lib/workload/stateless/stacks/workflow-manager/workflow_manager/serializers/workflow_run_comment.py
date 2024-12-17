from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import WorkflowRunComment, WorkflowRun


class WorkflowRunCommentBaseSerializer(SerializersBase):
    pass


class WorkflowRunCommentMinSerializer(WorkflowRunCommentBaseSerializer):
    class Meta:
        model = WorkflowRunComment
        fields = ["orcabus_id", "comment", "timestamp"]


class WorkflowRunCommentSerializer(WorkflowRunCommentBaseSerializer):
    class Meta:
        model = WorkflowRunComment
        fields = "__all__"
