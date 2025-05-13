from sequence_run_manager.serializers.base import SerializersBase, OrcabusIdSerializerMetaMixin
from sequence_run_manager.models.sample_sheet import SampleSheet
from sequence_run_manager.serializers.comment import CommentSerializer
class SampleSheetBaseSerializer(SerializersBase):
    pass

class SampleSheetSerializer(SampleSheetBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = SampleSheet
        fields = "__all__"
        
class SampleSheetWithCommentSerializer(SampleSheetBaseSerializer):
    comment = CommentSerializer(read_only=True)
    
    class Meta(OrcabusIdSerializerMetaMixin):
        model = SampleSheet
        fields = "__all__"
        include_comment = True