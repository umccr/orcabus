from rest_framework import serializers

from sequence_run_manager.models import Comment
from sequence_run_manager.serializers.base import SerializersBase, OptionalFieldsMixin

class CommentBaseSerializer(SerializersBase):
    orcabus_id_prefix = Comment.orcabus_id_prefix

class CommentSerializer(CommentBaseSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
        
