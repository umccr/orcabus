from sequence_run_manager.models import Comment
from sequence_run_manager.serializers.base import SerializersBase, OrcabusIdSerializerMetaMixin


class CommentBaseSerializer(SerializersBase):
    pass


class CommentSerializer(CommentBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Comment
        fields = "__all__"
