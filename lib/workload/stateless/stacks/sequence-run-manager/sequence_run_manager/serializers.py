from rest_framework import serializers

from sequence_run_manager.models import Sequence


class SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sequence
        fields = "__all__"
