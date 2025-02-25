from rest_framework import serializers

from sequence_run_manager.models import Sequence
from sequence_run_manager.serializers.base import SerializersBase, OptionalFieldsMixin, OrcabusIdSerializerMetaMixin


class SequenceBaseSerializer(SerializersBase):
    pass
    

class SequenceListParamSerializer(OptionalFieldsMixin, SequenceBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Sequence
        fields = "__all__"

class SequenceMinSerializer(SequenceBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Sequence
        fields = ["orcabus_id", "instrument_run_id", "start_time", "end_time", "status"]

class SequenceSerializer(SequenceBaseSerializer):
    libraries = serializers.ListField(read_only=True, child=serializers.CharField(), help_text="List of libraries associated with the sequence")
    
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Sequence
        fields = "__all__"
        include_libraries = True
    
    def get_libraries(self, obj):
        """
        Get all libraries associated with the sequence
        """
        return obj.libraries()
        
class SequenceRunCountByStatusSerializer(serializers.Serializer):
    all = serializers.IntegerField()
    started = serializers.IntegerField()
    succeeded = serializers.IntegerField()
    failed = serializers.IntegerField()
    aborted = serializers.IntegerField()
