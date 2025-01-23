from workflow_manager.serializers.base import SerializersBase, OrcabusIdSerializerMetaMixin
from workflow_manager.models import WorkflowRunComment, WorkflowRun


class WorkflowRunCommentBaseSerializer(SerializersBase):
    pass


class WorkflowRunCommentMinSerializer(WorkflowRunCommentBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = WorkflowRunComment
        fields = ["orcabus_id", "comment", "timestamp"]


class WorkflowRunCommentSerializer(WorkflowRunCommentBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = WorkflowRunComment
        fields = "__all__"
