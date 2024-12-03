from rest_framework import serializers

from sequence_run_manager.models import Sequence
from sequence_run_manager.serializers.base import SerializersBase, OptionalFieldsMixin


class SequenceBaseSerializer(SerializersBase):
    orcabus_id_prefix = Sequence.orcabus_id_prefix
    

class SequenceListParamSerializer(OptionalFieldsMixin, SequenceBaseSerializer):
    class Meta:
        model = Sequence
        fields = "__all__"

class SequenceMinSerializer(SequenceBaseSerializer):
    class Meta:
        model = Sequence
        fields = ["orcabus_id", "instrument_run_id", "start_time", "end_time", "status"]

class SequenceSerializer(SequenceBaseSerializer):
    class Meta:
        model = Sequence
        fields = "__all__"
        
    