from sequence_run_manager.serializers.base import SerializersBase, OrcabusIdSerializerMetaMixin
from sequence_run_manager.models.sample_sheet import SampleSheet

class SampleSheetBaseSerializer(SerializersBase):
    pass

class SampleSheetSerializer(SampleSheetBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = SampleSheet
        fields = "__all__"