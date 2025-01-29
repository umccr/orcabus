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
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Sequence
        fields = "__all__"
        
    